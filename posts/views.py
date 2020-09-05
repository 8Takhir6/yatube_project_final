from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator
from django.core.cache import caches
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Group, Post, User


# @cache_page(20)
def index(request):
    # cache = caches["default"]
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, "index.html", {"page": page, "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html",
                  {"page": page, "paginator": paginator, "group": group})


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            post_form_get = form.save(commit=False)
            post_form_get.author = request.user
            post_form_get.save()
            return redirect("index")
    return render(request, "posts/new.html", {"form": form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.order_by("-pub_date")
    paginator = Paginator(author_posts, 6)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "posts/profile.html",
                  {
                      "page": page,
                      "paginator": paginator,
                      "author": author,

                  })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.all()
    return render(request, "posts/post.html", {
        "post": post,
        "author": post.author,
        "items": comments,
        "form": CommentForm(),
    })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("post", username=username, post_id=post.id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post
                    )
    form_context = {"form": form, "post": post, "post_edit": True}

    if request.method == "POST":
        if form.is_valid():
            post.save()
            return redirect("post", username=post.author,
                            post_id=post.id
                            )
        return render(request, "posts/new.html", form_context)

    return render(request, "posts/new.html", form_context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('post', username=username, post_id=post_id)


def page_not_found(request, exception):  # noqa
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
