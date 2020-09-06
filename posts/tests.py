from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User


class UsersTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test user")
        self.authorized_client = Client()
        self.unauthorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text="test text1",
            author=self.user
        )
        self.post_id = self.post.id
        self.group = Group.objects.create(
            title='Test group',
            slug='test-group',
            description='test description'
        )

    def post_search(self, url):
        cache.clear()
        response = self.authorized_client.get(url)
        return self.assertContains(response, self.post.text)

    def test_creation_profile(self):
        cache.clear()
        response = self.authorized_client.get(
            reverse('profile', kwargs={"username": self.user.username}))
        self.assertEqual(response.status_code, 200)

    def test_post_creation_user(self):
        cache.clear()
        response = self.authorized_client.post(reverse("new_post"),
                                               {"group": self.group.id,
                                                "text": "Test text"},
                                               follow=True)
        self.assertEqual(Post.objects.filter(text="Test text").count(), 1)

    def test_post_creation_not_user(self):
        cache.clear()
        response = self.unauthorized_client.post(reverse("new_post"),
                                                 {"group": self.group.id,
                                                  "text": "Test text2"},
                                                 follow=True)
        self.assertNotEqual(Post.objects.filter(text="Test text2").count(), 1)

    def test_new_post(self):
        cache.clear()
        new_post = self.post
        url_list = (
            reverse('index'),
            reverse('profile', kwargs={"username": self.user.username}),
            reverse('post', kwargs={"username": self.user.username,
                                    "post_id": new_post.id, })
        )
        for url in url_list:
            self.post_search(url)

    def test_change_post(self):
        cache.clear()
        edit_post = self.authorized_client.post(
            reverse("post_edit", args=[self.user.username, self.post.id]),
            {"group": "test group2",
             "text": "Test text"}, follow=True
        )
        url_list = (
            reverse('index'),
            reverse('profile', kwargs={"username": self.user.username}),
            reverse('post', kwargs={"username": self.user.username,
                                    "post_id": self.post.id})
        )
        for url in url_list:
            self.post_search(url)

    def test_server_return_404(self):
        cache.clear()
        response = self.authorized_client.get("does_not_exist_url/")
        self.assertEqual(response.status_code, 404)


class ImageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="yser")
        self.client.force_login(self.user)

    def test_post_with_image(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )

        img = SimpleUploadedFile(
            name="some.gif",
            content=small_gif,
            content_type="image/gif"
        )

        post = Post.objects.create(
            author=self.user,
            text="text",
            image=img,
        )

        urls = [
            reverse("post", args=[self.user.username, post.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                cache.clear()
                response = self.client.get(url)
                self.assertContains(response, "<img")

    def test_post_without_image(self):
        not_image = SimpleUploadedFile(
            name="some.txt",
            content=b'abc',
            content_type="text/plane"
        )

        url = reverse("new_post")
        cache.clear()
        response = self.client.post(
            url, {"text": "some_text", "image": not_image},
        )
        self.assertFormError(
            response,
            "form",
            "image",
            errors=(
                "Загрузите правильное изображение. Файл, который "
                "вы загрузили, поврежден или не является изображением."
            )
        )


class CacheTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="yser",
            password="test_pass"
        )
        self.client.force_login(self.user)

    def test_cache_index(self):
        response = self.client.get(reverse("index"))
        self.post_check = Post.objects.create(
            text="New post",
            author=self.user
        )
        self.assertNotContains(response, "New post")
        cache.clear()
        response_after_clear = self.client.get(reverse("index"))
        self.assertContains(response_after_clear, self.post_check.text)


class Project06Test(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="yser",
            password="test_pass"
        )
        self.following_user = User.objects.create_user(
            username="following_user",
            password="test_pass"
        )
        self.post = Post.objects.create(
            text="test text1",
            author=self.following_user
        )
        cache.clear()

    def test_auth_user_following(self):
        self.client.force_login(self.user)
        author = get_object_or_404(User, username=self.following_user.username)
        following = self.client.get(
            reverse("profile_follow", args=[self.following_user.username]))
        response = Follow.objects.filter(user=self.user,
                                         author=author).exists()
        self.assertEqual(response, True)

    def test_auth_user_unfollowing(self):
        self.client.force_login(self.user)
        author = get_object_or_404(User, username=self.following_user.username)
        following = self.client.get(
            reverse("profile_follow", args=[self.following_user.username]))
        unfollowing = self.client.get(
            reverse("profile_unfollow", args=[self.following_user.username]))
        response = Follow.objects.filter(user=self.user,
                                         author=author).exists()
        self.assertEqual(response, False)

    def test_post_in_follow_index(self):
        self.client.force_login(self.user)
        following = self.client.get(
            reverse("profile_follow", args=[self.following_user.username]))
        response = self.client.get(reverse("follow_index"))
        self.assertContains(response, self.post.text)

    def test_post_not_in_follow_index(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("follow_index"))
        self.assertNotContains(response, self.post.text)

    def test_add_comment_auth_user(self):
        self.client.force_login(self.user)
        add_comment = self.client.post(
            reverse("add_comment", args=[self.post.author, self.post.id]),
            {'text': 'new_comment'}
        )
        response = Comment.objects.filter(author=self.user,
                                          post=self.post).exists()
        self.assertEqual(response, True)
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, "new_comment")
        self.assertEqual(comment.author, self.user)

    def test_add_comment_not_auth_user(self):
        add_comment = self.client.post(
            reverse("add_comment", args=[self.post.author, self.post.id]),
            {'text': 'new_comment'}
        )
        self.assertEqual(add_comment.status_code, 302)
        comment = Comment.objects.count()
        self.assertEqual(comment, 0)
