from django.forms import ModelForm, Textarea

from posts.models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ("group", "text", "image")
        labels = {
            "group": "Группа",
            "text": "Текст поста",
            "image": "Пссс! Вставляй пикчу"
        }
        help_texts = {
            "group": "Укажите принадлежность к группе",
            "text": "Пишите пост тут",
            "image": "Выберите изображение"
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
        labels = {'text': 'Текст комментария'}
        widgets = {'text': Textarea}
