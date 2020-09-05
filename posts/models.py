from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, unique=True, null=True)
    slug = models.SlugField(max_length=40, unique=True, null=True)
    description = models.TextField(max_length=2000, blank=True, null=True)

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name="Текст Поста", )
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, blank=True, null=True,
                               on_delete=models.SET_NULL,
                               verbose_name="Автор поста",
                               related_name="posts")
    group = models.ForeignKey(Group, blank=True, null=True,
                              on_delete=models.SET_NULL,
                              verbose_name="Группа",
                              related_name="posts")
    image = models.ImageField(upload_to='posts/', verbose_name="Изображение",
                              blank=True, null=True)

    def __str__(self):
        return self.text

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(Post, blank=True, null=True,
                             on_delete=models.CASCADE,
                             related_name="comments")
    author = models.ForeignKey(User, blank=True, null=True,
                               on_delete=models.CASCADE,
                               related_name="comments")
    text = models.TextField(verbose_name="Текст комментария", )
    created = models.DateTimeField("date published", auto_now_add=True)
