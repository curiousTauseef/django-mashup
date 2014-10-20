from django.test import TestCase

from .views import Mashup, HTMLView, ViewView, URLView, TOKEN_LENGTH


class DummyGetRequest():
    method = "GET"


class DummyPostRequest():
    method = "POST"


class DummyDeleteRequest():
    method = "DELETE"


class MyMashup(Mashup):
    views = [HTMLView("<p>This is a bunch of html<p>", container="<div class='first-mash'>" + HTMLView.content_sub_string + "</div>"),
             HTMLView("<p>This is another bunch of html</p>", container="<div class='second-mash'>" + HTMLView.content_sub_string + "</div>"),
             ]


class MySecondMashup(Mashup):
    views = [ViewView(MyMashup, container="<div class='big-mash-container'>" + ViewView.content_sub_string + "</div>"),
             HTMLView("<p>A third bunch of HTML</p>"),
             ]


class MyThirdMashup(Mashup):

    views = [URLView("/testing/url", container="<div class='big-mash-container'>" + URLView.content_sub_string + "</div>"),
             URLView("/test/url"),
             ]


class MyMashupContained(MyMashup):
    containers = ("<div id=first-view-container>{{ mashup }}</div>",
                  "<div id=second-view-container>{{ mashup }}</div>")


class MySecondMashupContained(MySecondMashup):
    containers = ("<div id=first-second-view-container>{{ mashup }}</div>",
                  "<div id=second-second-view-container>{{ mashup }}</div>")


class MyGetPostMashup(Mashup):
    get_views = MyMashup.views
    post_views = MySecondMashup.views


class MyGetPostMashupContained(Mashup):
    get_views = MyMashup.views
    post_views = MySecondMashup.views

    get_containers = MyMashupContained.containers
    post_containers = MySecondMashupContained.containers


class MashupViewTests(TestCase):

    def test_html_view_mashing(self):

        # Assert that MyMashup gives the expected response
        self.assertEqual(MyMashup.as_view()(DummyGetRequest()).content,
                         b"<div class='first-mash'><p>This is a bunch of html<p></div><div class='second-mash'><p>This is another bunch of html</p></div>")

    def test_view_view_mashing(self):
        # This test might fail because of a failure in HTMLView
        # If both this test and test_html_view_mashing fails, address test_html_view_mashing first

        # Assert that MySecondMashup gives the expected response.
        self.assertEqual(MySecondMashup.as_view()(DummyGetRequest()).content,
                         b"<div class='big-mash-container'><div class='first-mash'><p>This is a bunch of html<p></div><div class='second-mash'><p>This is another bunch of html</p></div></div><p>A third bunch of HTML</p>")

    def test_url_view(self):
        # Tough to test URL view.
        # For now, we'll assert that we got something of the right length out of it.
        dummy_token = ''.join(" " for _ in range(TOKEN_LENGTH))

        target_length = 0
        for view in MyThirdMashup.views:
            expected_content = view.jquery_detector % (view.jquery_loader, view.javascript_loader)
            expected_content = expected_content.replace(URLView.token_sub_string, dummy_token)
            expected_content = expected_content .replace(URLView.url_sub_string, view.content)

            target_length += len(expected_content)

            if hasattr(view, "container") and view.container:
                target_length += len(view.container.replace(view.content_sub_string, ""))

        # Assert that the response has the correct length
        self.assertEqual(len(MyThirdMashup.as_view()(DummyGetRequest()).content), target_length)


class MashupComponentInitTests(TestCase):

    def test_container_subclassing(self):

        class MyHTMLView(HTMLView):
            container = "test_container"

        htmlview = HTMLView("some content")
        myhtmlview = MyHTMLView("some content")
        mysecondhtmlview = MyHTMLView("some content", container="test_container_2")

        # Assert that the instance of HTMLView has no container
        self.assertTrue((not hasattr(htmlview, "container")) or (not htmlview.container))
        # Assert that the first instance of MyHTMLView has the container we gave it.
        self.assertEqual(myhtmlview.container, "test_container")
        # Assert that the second instance of MyHTMLView has the container we gave it.
        self.assertEqual(mysecondhtmlview.container, "test_container_2")

    def test_mashup_containers(self):

        self.assertEqual(MyMashupContained.as_view()(DummyGetRequest()).content,
                         b"<div id=first-view-container><div class='first-mash'><p>This is a bunch of html<p></div></div><div id=second-view-container><div class='second-mash'><p>This is another bunch of html</p></div></div>")

        self.assertEqual(MySecondMashupContained.as_view()(DummyGetRequest()).content,
                         b"<div id=first-second-view-container><div class='big-mash-container'><div class='first-mash'><p>This is a bunch of html<p></div><div class='second-mash'><p>This is another bunch of html</p></div></div></div><div id=second-second-view-container><p>A third bunch of HTML</p></div>")


class MashupGetVsPost(TestCase):

    def test_get_vs_post_views(self):

        # Assert that MyGetPostMashup gives the correct response to a GET
        self.assertEqual(MyGetPostMashup.as_view()(DummyGetRequest()).content,
                         b"<div class='first-mash'><p>This is a bunch of html<p></div><div class='second-mash'><p>This is another bunch of html</p></div>")

        # Assert that MyGetPostMashup gives the correct response to a POST
        self.assertEqual(MyGetPostMashup.as_view()(DummyPostRequest()).content,
                         b"<div class='big-mash-container'><div class='first-mash'><p>This is a bunch of html<p></div><div class='second-mash'><p>This is another bunch of html</p></div></div><p>A third bunch of HTML</p>")

        # Assert that MyGetPostMashup gives the correct response to a DELETE
        self.assertEqual(MyGetPostMashup.as_view()(DummyDeleteRequest()).content, b"")

    def test_get_vs_post_containers(self):
        self.assertEqual(MyGetPostMashupContained.as_view()(DummyGetRequest()).content,
                         b"<div id=first-view-container><div class='first-mash'><p>This is a bunch of html<p></div></div><div id=second-view-container><div class='second-mash'><p>This is another bunch of html</p></div></div>")

        self.assertEqual(MyGetPostMashupContained.as_view()(DummyPostRequest()).content,
                         b"<div id=first-second-view-container><div class='big-mash-container'><div class='first-mash'><p>This is a bunch of html<p></div><div class='second-mash'><p>This is another bunch of html</p></div></div></div><div id=second-second-view-container><p>A third bunch of HTML</p></div>")

