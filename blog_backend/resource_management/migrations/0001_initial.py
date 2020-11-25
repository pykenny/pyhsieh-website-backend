# Generated by Django 3.1.3 on 2020-11-25 00:41

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('synonym', models.SlugField(max_length=100, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag_name', models.CharField(max_length=50, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CompiledArticleData',
            fields=[
                ('article', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='compiled_data', related_query_name='compile_article_data', serialize=False, to='resource_management.article')),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('data', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RawArticleData',
            fields=[
                ('article', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, primary_key=True, related_name='raw_data', related_query_name='raw_article_data', serialize=False, to='resource_management.article')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('version', models.CharField(max_length=30)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('data', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('deleted', models.DateTimeField(editable=False, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('alias', models.CharField(max_length=100)),
                ('extension', models.CharField(max_length=10)),
                ('resolution', models.IntegerField(choices=[(1, 'Original'), (2, 'Low'), (3, 'Medium'), (4, 'Large'), (5, 'High')])),
                ('height', models.PositiveIntegerField(null=True)),
                ('width', models.PositiveIntegerField(null=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', related_query_name='image', to='resource_management.article')),
            ],
        ),
        migrations.CreateModel(
            name='ArticleTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tags_of_article', related_query_name='article_tag', to='resource_management.article')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='articles_of_tag', related_query_name='article_tag', to='resource_management.tag')),
            ],
        ),
        migrations.CreateModel(
            name='ArticleEditHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('previous_title', models.CharField(max_length=200, null=True)),
                ('previous_synonym', models.SlugField(max_length=100, null=True)),
                ('previous_version', models.CharField(max_length=30, null=True)),
                ('update_data', models.TextField(null=True)),
                ('recover_data', models.TextField(null=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='edit_histories', related_query_name='article_edit_history', to='resource_management.article')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='image',
            index=models.Index(fields=['article', 'alias'], name='idx_image_resolution_group'),
        ),
        migrations.AddIndex(
            model_name='image',
            index=models.Index(fields=['article', 'alias', 'resolution'], name='idx_image_identity'),
        ),
        migrations.AddConstraint(
            model_name='articletag',
            constraint=models.UniqueConstraint(fields=('article', 'tag'), name='identity'),
        ),
    ]
