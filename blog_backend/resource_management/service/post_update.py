import os
import os.path
from collections import ItemsView
from pathlib import Path
import logging
from itertools import groupby, chain
from json import (
    load as json_load,
)
import tarfile
from tarfile import TarFile, TarInfo  # typing
from typing import (
    final,
    Final,
    NamedTuple,
    IO,
    Tuple,
    Dict,
    List,
    Set,
    Iterable,
    Optional,
    Any,
    Union,
)

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models.query import QuerySet
from safedelete.queryset import SafeDeleteQueryset

from resource_management.models import (
    Article,
    RawArticleData,
    ArticleEditHistory,
    CompiledArticleData,
    Tag,
    ArticleTag,
    Image,
)

from resource_management.model_operations.articles import (
    ArticleOperations,
    RawArticleDataOperations,
    CompiledArticleDataOperations,
)
from resource_management.model_operations import (
    TagOperations,
    ArticleTagOperations,
    ImageOperations,
)

from resource_management.utils.images import (
    resize_image,
    image_compare,
    save_image,
    get_image_full_path,
)

from resource_management.utils.articles import DocumentPatchCreator, PatchResult

from bs4 import BeautifulSoup
from bs4.element import ResultSet  # Typing
from PIL import Image as PILImage

__all__ = [
    "PostUpdateHandler",
]


# CONSTANTS
_META_FILENAME: Final = "meta.json"
_IMG_SOURCE_PATH: Final = "img"
_RAW_DOC_FILENAME: Final = "document.md"
_COMPILED_DOC_FILENAME: Final = "document.xml"

_META_TITLE_KEY: Final = "documentTitle"
_META_TAGS_KEY: Final = "documentTags"
_META_IMAGE_ALIAS_MAPPING_KEY: Final = "aliasMapping"
_META_VERSION_KEY: Final = "version"

_HTML_IMAGE_TAG: Final = "img"
_HTML_IMAGE_CLASS_ATTR: Final = "class"
_HTML_IMAGE_ALIAS_ATTR: Final = "alias"
_HTML_IMAGE_SRC_ATTR: Final = "src"
_HTML_IMAGE_SRCSET_ATTR: Final = "data-srcset"
_HTML_LAZYLOAD_SIZE_ATTR: Final = "data-sizes"

_IMG_URL_ROUTE: Final = "/img/"

_CLASS_LAZYLOAD: Final = "lazyload"
_LAZYLOAD_SIZE_AUTO: Final = "auto"

_SRC_FORMAT: Final = "{img_route:s}{{file_name:s}}".format(
    img_route=_IMG_URL_ROUTE,
)
_SRCSET_FORMAT: Final = "{img_route:s}{{file_name:s}} {{width:d}}w".format(
    img_route=_IMG_URL_ROUTE,
)

# LOGGING
logging.basicConfig(level=logging.NOTSET)
_LOGGER = logging.getLogger()


@final
class ValidatedDocument(NamedTuple):
    title: str
    tags: List[str]
    version: str
    raw_document: str
    content_xml: BeautifulSoup
    image_info: Dict[str, TarInfo]
    image_tags: ResultSet


@final
class PostUpdateHandler(object):
    @classmethod
    def upload_article(
        cls, bundle: str, doc_synonym: str, create_only: bool = False
    ) -> None:
        _LOGGER.info("Reading target archive file...")
        with tarfile.open(bundle, "r:gz") as archive:
            # Step 1: Validate archive and create parsed data (JSON, XML, ...)
            _LOGGER.info("Validating archive...")
            validated_doc = cls._validate_archive(archive)
            # Step 2: Is this a new article, or existing one?
            update_flag = True
            target_article = None
            try:
                target_article = ArticleOperations.get_article_by_synonym(doc_synonym)
            except ObjectDoesNotExist:
                update_flag = False

            # The additional logic on target_article is to notify mypy
            # that target_article is Article instance, instead of None.
            if update_flag and target_article:
                if create_only:
                    raise ValueError(
                        "Article synonym '{synonym:s}' has been registered.".format(
                            synonym=doc_synonym
                        )
                    )
                _LOGGER.info(
                    "Synonym '{synonym:s}' has been registered. "
                    "Try to update existing entry...".format(synonym=doc_synonym)
                )
                cls._update_article(target_article, validated_doc, archive)
            else:
                _LOGGER.info(
                    "Synonym '{synonym:s}' has not been registered. "
                    "Start creating new article entry...".format(synonym=doc_synonym)
                )
                cls._create_article(doc_synonym, validated_doc, archive)

    @classmethod
    def _extractfile(cls, archive: TarFile, file_info: TarInfo) -> IO[bytes]:
        """ Wrapper on TarFile.extractfile() to guarantee IO handle is returned. """
        stream = archive.extractfile(file_info)
        if not stream:
            raise ValueError("file_info does not reference to regular file or link.")

        return stream

    @classmethod
    def _get_parsed_meta(cls, archive: TarFile) -> Dict[str, Any]:
        file_info = archive.getmember(_META_FILENAME)
        with cls._extractfile(archive, file_info) as r_stream:
            return json_load(r_stream)

    @classmethod
    def _get_raw_document(cls, archive: TarFile) -> str:
        file_info = archive.getmember(_RAW_DOC_FILENAME)
        with cls._extractfile(archive, file_info) as r_stream:
            return r_stream.read().decode("utf-8")

    @classmethod
    def _get_parsed_xml_document(cls, archive: TarFile) -> BeautifulSoup:
        file_info = archive.getmember(_COMPILED_DOC_FILENAME)
        with cls._extractfile(archive, file_info) as r_stream:
            return BeautifulSoup(r_stream, "html.parser")

    @staticmethod
    def _get_image_info(archive: TarFile, img_name: str) -> TarInfo:
        return archive.getmember("/".join([_IMG_SOURCE_PATH, img_name]))

    @classmethod
    def _validate_archive(cls, archive: TarFile) -> ValidatedDocument:
        # Step 1: Make sure the archive meets all basic requirements
        meta = cls._get_parsed_meta(archive)
        raw_document = cls._get_raw_document(archive)
        content_xml = cls._get_parsed_xml_document(archive)
        title: str = meta[_META_TITLE_KEY]
        tags: List[str] = meta[_META_TAGS_KEY]
        version: str = meta[_META_VERSION_KEY]
        image_alias_mapping: Dict[str, str] = meta[_META_IMAGE_ALIAS_MAPPING_KEY]

        # Step 2: Make sure image tags have proper reference to file
        #         info in the archive.
        image_info: Dict[str, TarInfo] = {}
        image_tags = content_xml.find_all(_HTML_IMAGE_TAG)
        for image_tag in image_tags:
            image_alias = image_tag[_HTML_IMAGE_ALIAS_ATTR]
            image_info[image_alias] = cls._get_image_info(
                archive, image_alias_mapping[image_alias]
            )

        # If no error occur during this step, we're fine to return all the information
        return ValidatedDocument(
            title, tags, version, raw_document, content_xml, image_info, image_tags
        )

    @classmethod
    def _update_article(
        cls, target_article: Article, validated_doc: ValidatedDocument, archive: TarFile
    ) -> None:
        # Most of the uninitialized data here are used as indicator of
        # article update.
        original_title: Optional[str] = None
        original_version: Optional[str] = None
        edit_patches: Optional[PatchResult] = None
        edit_history_entry: Optional[ArticleEditHistory] = None
        created_image_entries: Optional[List[Image]] = None
        created_image_buffers: Optional[List[PILImage.Image]] = None

        # Update Article entry as needed (title)
        if target_article.title != validated_doc.title:
            _LOGGER.info(
                "Title Changed: {old_title:s} -> {new_title:s}".format(
                    old_title=target_article.title, new_title=validated_doc.title
                )
            )
            original_title = target_article.title
            target_article.title = validated_doc.title

        # Update raw document entry as needed (version / raw data)
        raw_document = RawArticleDataOperations.get_raw_data(target_article)
        if raw_document.data != validated_doc.raw_document:
            _LOGGER.info("Detect modification on raw Markdown file. Creating patch...")
            edit_patches = DocumentPatchCreator().create_patch_files(
                validated_doc.raw_document, validated_doc.raw_document
            )
            raw_document.data = validated_doc.raw_document
        if raw_document.version != validated_doc.version:
            _LOGGER.info(
                "Version Changed: {old_version:s} -> {new_version:s}".format(
                    old_version=raw_document.version, new_version=validated_doc.version
                )
            )
            original_version = raw_document.version
            raw_document.version = validated_doc.version

        # Create edit history as needed
        if original_title or edit_patches or original_version:
            _LOGGER.info("... New edit entry required.")
            edit_history_entry = ArticleEditHistory(
                previous_title=original_title,
                previous_version=original_version,
                update_data=edit_patches and edit_patches.update_patch,
                recover_data=edit_patches and edit_patches.recover_patch,
            )

        # Update image entries
        updated_images: Set[str] = set(validated_doc.image_info.keys())
        removed_images: Set[str] = set()  # Existing files require removal
        renewed_images: Set[str] = set()  # Existing files require update

        # Scan through original images to sort out groups require removal or renewal
        original_image_entries = ImageOperations.get_original_images(target_article)
        for entry in original_image_entries:
            if entry.alias in updated_images:
                updated_image_info = validated_doc.image_info[entry.alias]
                original_image_path = get_image_full_path(entry)
                with cls._extractfile(
                    archive, updated_image_info
                ) as updated_image_stream:
                    if not image_compare(updated_image_stream, original_image_path):
                        renewed_images.add(entry.alias)
                        _LOGGER.info(
                            "Detect image changed: {alias:s}".format(alias=entry.alias)
                        )
                    else:
                        updated_images.remove(entry.alias)
            else:
                removed_images.add(entry.alias)
                _LOGGER.info(
                    "Detect image removed: {alias:s}".format(alias=entry.alias)
                )

        created_images = updated_images - removed_images  # New + Renewed
        deleted_images = removed_images | renewed_images  # Removed + Renewed
        removed_image_entries = ImageOperations.get_images_by_article_and_aliases(
            target_article, aliases=deleted_images, include_original=True
        )
        kept_image_entries = (
            ImageOperations.get_images_by_article(target_article, include_original=True)
            .exclude(alias__in=(created_images | deleted_images))
            .order_by("alias", "resolution")
        )

        if created_images:
            created_image_entries, created_image_buffers = cls._create_image_data(
                target_article,
                validated_doc.image_info,
                archive,
                filter_list=created_images,
            )

        # We need to update the compiled document when meeting one of the conditions:
        # 1. Version changed (output XML structure can be changed)
        # 2. Change on raw Markdown document
        # 3. New image entry created (adding new alias, or file update on existing ones)
        # 4. Removal of existing image
        compiled_document: Optional[CompiledArticleData] = None
        if original_version or edit_patches or created_images or removed_images:
            compiled_document = CompiledArticleDataOperations.get_compiled_data(
                target_article
            )

        kept_tags: Set[str] = set(
            ArticleTagOperations.get_tag_relations_from_article(
                target_article, prefetch_tags=True
            )
            .filter(tag__tag_name__in=validated_doc.tags)
            .values_list("tag__tag_name", flat=True)
        )
        removed_tag_relations: "QuerySet[ArticleTag]" = (
            ArticleTagOperations.get_tag_relations_from_article(
                target_article, prefetch_tags=True
            ).exclude(tag__tag_name__in=validated_doc.tags)
        )
        removed_tags: Set[str] = set(
            entry.tag.tag_name for entry in removed_tag_relations
        )
        created_tags: Set[str] = set(validated_doc.tags) - kept_tags - removed_tags
        _LOGGER.info(
            "Kept tags: {0:s}\nRemoved tags: {1:s}\nCreated tags: {2:s}".format(
                ", ".join(kept_tags), ", ".join(removed_tags), ", ".join(created_tags)
            )
        )

        # Finally, update article entry if we really update anything
        article_updated: Optional[Article] = None
        if (
            original_title  # Article
            or (edit_patches or original_version)  # Raw Data
            or (removed_tags or created_tags)  # Tags
            or (created_images or removed_images)  # Images
        ):
            article_updated = target_article

        raw_document_updated: Optional[RawArticleData] = None
        if edit_patches or original_version:
            raw_document_updated = raw_document

        write_success_flag: bool = False
        try:
            created_image_entries, update_flag = cls._run_write_operations(
                article_updated,
                validated_doc,
                raw_data_updated=raw_document_updated,
                compiled_data_updated=compiled_document,
                edit_data_created=edit_history_entry,
                tags_updated=validated_doc.tags,
                article_tags_deleted=removed_tag_relations,
                images_created=created_image_entries,
                images_kept=kept_image_entries,
                images_deleted=removed_image_entries,
            )
            if created_image_entries and created_image_buffers:
                cls._save_images(
                    created_image_buffers,
                    created_image_entries,
                    validated_doc.image_info,
                    archive,
                )
            if not update_flag:
                _LOGGER.info("No required update detected.")
            write_success_flag = True
        finally:
            if not write_success_flag:
                cls._error_cleanup(created_image_entries)

    @classmethod
    def _create_article(
        cls, doc_synonym: str, validated_doc: ValidatedDocument, archive: TarFile
    ) -> None:
        article = Article(
            synonym=doc_synonym,
            title=validated_doc.title,
        )
        raw_data = RawArticleData(
            article=article,
            version=validated_doc.version,
            data=validated_doc.raw_document,
        )
        tags_updated = validated_doc.tags
        _LOGGER.info(
            "Article tags: {tag_list:s} .".format(tag_list=", ".join(tags_updated))
        )
        _LOGGER.info(
            "Loading data of {num_images:d} images...".format(
                num_images=len(validated_doc.image_info)
            )
        )
        image_entries, image_buffers = cls._create_image_data(
            article, validated_doc.image_info, archive
        )

        write_success_flag: bool = False
        try:
            _LOGGER.info("Handling DB write operations...")
            updated_image_entries, update_flag = cls._run_write_operations(
                article,
                validated_doc,
                raw_data_updated=raw_data,
                tags_updated=tags_updated,
                images_created=image_entries,
            )
            _LOGGER.info("Done with writing to the DB.")
            _LOGGER.info("Handling image saving...")
            # Logic here is to ensure mypy we're using non-None input on
            # buffers and entries
            if image_buffers and updated_image_entries:
                num_saved_images = cls._save_images(
                    image_buffers,
                    updated_image_entries,
                    validated_doc.image_info,
                    archive,
                )
                _LOGGER.info(
                    "Complete saving {num_saved_images:d} images.".format(
                        num_saved_images=num_saved_images,
                    )
                )
            write_success_flag = True
        finally:
            if not write_success_flag:
                _LOGGER.error(
                    "Error happened during writing process. Running cleanup..."
                )
                cls._error_cleanup(image_entries)

    @classmethod
    @transaction.atomic
    def _process_compiled_data(
        cls,
        target_article: Article,
        compiled_entry: Optional[CompiledArticleData],
        image_entries: Iterable[Image],
        validated_doc,
    ) -> None:
        # Only call this function when you're sure to add/update compiled content.
        compiled_entry = compiled_entry or CompiledArticleData(article=target_article)
        alias_attr_mapping = cls._generate_alias_attribute_mapping(image_entries)
        cls._convert_article_xml(validated_doc.image_tags, alias_attr_mapping)
        compiled_entry.data = validated_doc.content_xml.prettify()
        compiled_entry.save()

    @classmethod
    @transaction.atomic
    def _run_write_operations(
        cls,
        target_article: Optional[Article],
        validated_doc: ValidatedDocument,
        raw_data_updated: Optional[RawArticleData] = None,
        edit_data_created: Optional[ArticleEditHistory] = None,
        compiled_data_updated: Optional[CompiledArticleData] = None,
        tags_updated: Optional[Iterable[str]] = None,
        article_tags_deleted: Optional[QuerySet[ArticleTag]] = None,
        images_kept: Optional[SafeDeleteQueryset[Image]] = None,
        images_created: Optional[List[Image]] = None,
        images_deleted: Optional[SafeDeleteQueryset[Image]] = None,
    ) -> Tuple[Optional[List[Image]], bool]:
        """Wrap all create/update/deletion operations here to make the
        full writing process atomic.
        """

        # Only run DB operation when target_article is assigned
        if target_article is None:
            return None, False

        # We need this flag to identify raw data, compiled data, and
        # article-tag relations are created or updated
        is_new_article = target_article.id is None
        target_article.save()

        if raw_data_updated:
            if is_new_article:
                raw_data_updated.article = target_article
            raw_data_updated.save()

        if edit_data_created:
            # We don't modify existing data and only create new records.
            edit_data_created.article = target_article
            edit_data_created.save()

        tag_entries: List[Tag] = []
        if tags_updated:
            tag_entries = TagOperations.bulk_loose_create(
                {"tag_name": tag_name} for tag_name in tags_updated
            )

        if article_tags_deleted:
            article_tags_deleted.delete()

        if tags_updated:
            if is_new_article:
                ArticleTagOperations.bulk_create(
                    ArticleTag(article=target_article, tag=tag_entry)
                    for tag_entry in tag_entries
                )
            else:
                ArticleTagOperations.bulk_loose_create(
                    {"article": target_article, "tag": tag_entry}
                    for tag_entry in tag_entries
                )

        if images_deleted:
            images_deleted.delete()

        if images_created:
            for image_entry in images_created:
                image_entry.article = target_article
            images_created = ImageOperations.bulk_create(images_created)

        # Image data's ready. Modify converted XML then dump to DB entry as needed.
        if is_new_article or compiled_data_updated:
            _LOGGER.info("Need to create or update compiled XML. Processing...")
            image_entries = chain(
                images_created or (),
                images_kept or (),
            )
            cls._process_compiled_data(
                target_article,
                compiled_data_updated,
                image_entries,
                validated_doc,
            )

        return images_created, True

    @classmethod
    def _save_images(
        cls,
        image_buffers: List[PILImage.Image],
        image_entries: List[Image],
        image_info: Dict[str, TarInfo],
        archive: TarFile,
    ) -> int:
        for image_buffer, image_entry in zip(image_buffers, image_entries):
            # To copy the original file, we need to stream data from archive
            # instead of copying from PIL.Image buffer.
            if image_entry.resolution == Image.ImageResolutionType.ORIGINAL:
                with cls._extractfile(
                    archive, image_info[image_entry.alias]
                ) as image_stream:
                    save_image(image_entry, img_stream=image_stream)
                    _LOGGER.info(
                        "Original image '{file_name:s}'({alias:s}) saved.".format(
                            file_name=image_entry.file_name,
                            alias=image_entry.alias,
                        )
                    )
            else:
                save_image(image_entry, image_buffer)
                _LOGGER.info(
                    "Resized image '{file_name:s}({alias:s}/{resolution:s})' saved.".format(
                        file_name=image_entry.file_name,
                        alias=image_entry.alias,
                        resolution=Image.ImageResolutionType(
                            image_entry.resolution
                        ).name,
                    )
                )

        return len(image_entries)

    @classmethod
    def _create_image_data(
        cls,
        article: Optional[Article],
        image_info: Dict[str, TarInfo],
        archive: TarFile,
        filter_list: Optional[Iterable[str]] = None,
    ) -> Tuple[List[Image], List[PILImage.Image]]:
        image_entries = []
        image_buffers = []

        image_info_iter: Union[
            Iterable[Tuple[str, TarInfo]], ItemsView[str, TarInfo]
        ] = image_info.items()
        if filter_list:
            image_info_iter = (
                (alias, file_info)
                for alias, file_info in image_info.items()
                if (alias in filter_list)
            )

        for alias, file_info in image_info_iter:
            resize_data = resize_image(cls._extractfile(archive, file_info)).items()
            for resolution, image_buffer in resize_data:
                image_entries.append(
                    Image(
                        article=article,
                        alias=alias,
                        extension=os.path.splitext(file_info.name)[1].replace(".", ""),
                        resolution=resolution,
                        height=image_buffer.size[0],
                        width=image_buffer.size[1],
                    )
                )
                image_buffers.append(image_buffer)

        return image_entries, image_buffers

    @staticmethod
    def _convert_article_xml(
        image_tags: ResultSet, alias_attr_mapping: Dict[str, Dict[str, str]]
    ) -> None:
        for image_tag in image_tags:
            # Update attributes, then drop alias
            alias = image_tag[_HTML_IMAGE_ALIAS_ATTR]
            image_tag.attrs.update(alias_attr_mapping[alias])
            del image_tag[_HTML_IMAGE_ALIAS_ATTR]

    @staticmethod
    def _image_entry_grouping_by_alias(entry: Image) -> str:
        return entry.alias

    @classmethod
    def _generate_alias_attribute_mapping(
        cls,
        entry_list: Iterable[Image],
    ) -> Dict[str, Dict[str, str]]:
        """Create mapping between image alias and attributes to be overwritten or
        updated to image elements in the parsed XML document.

        Note: It assumes the input list is sorted by (entry.alias, entry.resolution)
              so that (1) itertools.groupby() can work properly and 'data-srcset'
              options will be ordered by image resolution (width).
              As for responsive options, we'll let lazyload library help making the
              decision at the frontend (with 'auto' option on 'data-sizes' attribute).
        """
        alias_imgattr_mapping: Dict[str, Dict[str, str]] = {}
        for alias, entries in groupby(entry_list, cls._image_entry_grouping_by_alias):
            alias_imgattr_mapping[alias] = {
                _HTML_IMAGE_CLASS_ATTR: _CLASS_LAZYLOAD,
                _HTML_IMAGE_ALIAS_ATTR: alias,
                _HTML_IMAGE_SRC_ATTR: "",
                _HTML_IMAGE_SRCSET_ATTR: "",
                _HTML_LAZYLOAD_SIZE_ATTR: _LAZYLOAD_SIZE_AUTO,
            }
            srcset_tokens = []
            for entry in entries:
                if entry.resolution != Image.ImageResolutionType.ORIGINAL:
                    if entry.resolution == Image.ImageResolutionType.LOW:
                        alias_imgattr_mapping[alias][
                            _HTML_IMAGE_SRC_ATTR
                        ] = _SRC_FORMAT.format(file_name=entry.file_name)
                    srcset_tokens.append(
                        _SRCSET_FORMAT.format(
                            file_name=entry.file_name, width=entry.width
                        )
                    )
            alias_imgattr_mapping[alias][_HTML_IMAGE_SRCSET_ATTR] = ",".join(
                srcset_tokens
            )

        return alias_imgattr_mapping

    @staticmethod
    def _error_cleanup(image_entries: Optional[List[Image]]) -> None:
        if image_entries:
            for entry in image_entries:
                _LOGGER.warning(
                    "Try removing file '{file_name:s}'...".format(
                        file_name=entry.file_name
                    )
                )
                image_path = Path(get_image_full_path(entry))
                image_path.unlink(missing_ok=True)
