from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from posts.models import Group, Post, User


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
