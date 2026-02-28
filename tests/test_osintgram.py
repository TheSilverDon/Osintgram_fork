"""Mock-based integration tests for Osintgram.py.

These tests mock the Instagram Private API client to verify that each
Osintgram method correctly processes API responses, writes output files,
and dumps JSON. No real credentials or network access are required.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest


def _make_osintgram(tmp_path, write_file=False, json_dump=False):
    """Create an Osintgram instance with mocked API, bypassing __init__."""
    from src.Osintgram import Osintgram

    obj = object.__new__(Osintgram)
    obj.api = MagicMock()
    obj.api.username = "testuser"
    obj.api.authenticated_user_id = "999"
    obj.target = "targetuser"
    obj.target_id = 12345
    obj.is_private = False
    obj.following = True
    obj.writeFile = write_file
    obj.jsonDump = json_dump
    obj.cli_mode = True
    obj.output_dir = str(tmp_path / "output" / "targetuser")
    obj.geolocator = MagicMock()
    os.makedirs(obj.output_dir, exist_ok=True)
    return obj


# ---------------------------------------------------------------------------
# Sample data matching Instagram Private API response shapes
# ---------------------------------------------------------------------------

SAMPLE_FEED_ITEMS = [
    {
        "id": "post_1",
        "caption": {"text": "Hello world #travel #fun"},
        "comment_count": 5,
        "like_count": 100,
        "media_type": 1,
        "image_versions2": {"candidates": [{"url": "http://example.com/img1.jpg"}]},
        "location": {"lat": 40.7128, "lng": -74.0060},
        "taken_at": 1609459200,
    },
    {
        "id": "post_2",
        "caption": {"text": "Another post #travel"},
        "comment_count": 3,
        "like_count": 50,
        "media_type": 2,
        "image_versions2": {"candidates": [{"url": "http://example.com/img2.jpg"}]},
        "location": None,
        "taken_at": 1609545600,
    },
    {
        "id": "post_3",
        "caption": None,
        "comment_count": 0,
        "like_count": 25,
        "media_type": 1,
        "image_versions2": {"candidates": [{"url": "http://example.com/img3.jpg"}]},
        "taken_at": 1609632000,
    },
]

SAMPLE_COMMENTS = [
    {
        "user_id": 111,
        "user": {"pk": 111, "username": "commenter1", "full_name": "First Commenter"},
        "text": "Great post!",
    },
    {
        "user_id": 222,
        "user": {"pk": 222, "username": "commenter2", "full_name": "Second Commenter"},
        "text": "Nice one!",
    },
    {
        "user_id": 111,
        "user": {"pk": 111, "username": "commenter1", "full_name": "First Commenter"},
        "text": "Love it!",
    },
]

SAMPLE_USERS = [
    {"pk": 1001, "username": "follower1", "full_name": "Follower One"},
    {"pk": 1002, "username": "follower2", "full_name": "Follower Two"},
]


def _setup_single_page_feed(api_mock):
    api_mock.user_feed.return_value = {"items": SAMPLE_FEED_ITEMS, "next_max_id": None}


def _setup_single_page_comments(api_mock):
    api_mock.media_comments.return_value = {"comments": SAMPLE_COMMENTS, "next_max_id": None}


# ===========================================================================
# Test: get_captions
# ===========================================================================

class TestGetCaptions:
    def test_calls_user_feed(self, tmp_path):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        og.get_captions()
        og.api.user_feed.assert_called()

    def test_writes_captions_to_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        _setup_single_page_feed(og.api)
        og.get_captions()
        file_path = os.path.join(og.output_dir, "targetuser_captions.txt")
        assert os.path.isfile(file_path)
        content = open(file_path).read()
        assert "Hello world" in content
        assert "Another post" in content

    def test_dumps_captions_to_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        og.get_captions()
        json_path = os.path.join(og.output_dir, "targetuser_captions.json")
        assert os.path.isfile(json_path)
        data = json.load(open(json_path))
        assert "captions" in data
        # post_3 has caption=None, so only 2 captions
        assert len(data["captions"]) == 2

    def test_skips_null_captions(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        og.get_captions()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_captions.json")))
        assert len(data["captions"]) == 2


# ===========================================================================
# Test: get_total_comments
# ===========================================================================

class TestGetTotalComments:
    def test_sums_comment_counts(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        og.get_total_comments()
        captured = capsys.readouterr()
        assert "8" in captured.out   # 5+3+0
        assert "3" in captured.out   # 3 posts

    def test_writes_total_comments_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        _setup_single_page_feed(og.api)
        og.get_total_comments()
        file_path = os.path.join(og.output_dir, "targetuser_comments.txt")
        assert os.path.isfile(file_path)
        assert "8 comments" in open(file_path).read()

    def test_dumps_total_comments_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        og.get_total_comments()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_comments.json")))
        assert data["comment_counter"] == 8
        assert data["posts"] == 3


# ===========================================================================
# Test: get_comment_data
# ===========================================================================

class TestGetCommentData:
    def test_retrieves_comments_per_post(self, tmp_path):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_comment_data()
        assert og.api.media_comments.call_count == len(SAMPLE_FEED_ITEMS)

    def test_writes_comment_data_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_comment_data()
        file_path = os.path.join(og.output_dir, "targetuser_comment_data.txt")
        assert os.path.isfile(file_path)
        assert "commenter1" in open(file_path).read()

    def test_dumps_comment_data_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_comment_data()
        json_path = os.path.join(og.output_dir, "targetuser_comment_data.json")
        assert os.path.isfile(json_path)
        assert "commenter1" in open(json_path).read()

    def test_no_variable_shadowing(self, tmp_path):
        """Verify the comment loop variable is not overwritten (regression guard)."""
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_comment_data()
        # 3 comments x 3 posts = 9 total "Great post!" occurrences
        content = open(os.path.join(og.output_dir, "targetuser_comment_data.json")).read()
        assert content.count("Great post!") == 3


# ===========================================================================
# Test: get_followers
# ===========================================================================

class TestGetFollowers:
    def test_retrieves_followers(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_followers.return_value = {"users": SAMPLE_USERS, "next_max_id": None}
        from instagram_private_api import Client as AppClient
        with patch.object(AppClient, "generate_uuid", return_value="fake-token"):
            og.get_followers()
        captured = capsys.readouterr()
        assert "follower1" in captured.out
        assert "follower2" in captured.out

    def test_writes_followers_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        og.api.user_followers.return_value = {"users": SAMPLE_USERS, "next_max_id": None}
        from instagram_private_api import Client as AppClient
        with patch.object(AppClient, "generate_uuid", return_value="fake-token"):
            og.get_followers()
        file_path = os.path.join(og.output_dir, "targetuser_followers.txt")
        assert os.path.isfile(file_path)
        assert "follower1" in open(file_path).read()

    def test_dumps_followers_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        og.api.user_followers.return_value = {"users": SAMPLE_USERS, "next_max_id": None}
        from instagram_private_api import Client as AppClient
        with patch.object(AppClient, "generate_uuid", return_value="fake-token"):
            og.get_followers()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_followers.json")))
        assert "followers" in data
        assert len(data["followers"]) == 2

    def test_pagination(self, tmp_path):
        og = _make_osintgram(tmp_path)
        og.api.user_followers.side_effect = [
            {"users": [SAMPLE_USERS[0]], "next_max_id": "page2"},
            {"users": [SAMPLE_USERS[1]], "next_max_id": None},
        ]
        from instagram_private_api import Client as AppClient
        with patch.object(AppClient, "generate_uuid", return_value="fake-token"):
            og.get_followers()
        assert og.api.user_followers.call_count == 2


# ===========================================================================
# Test: get_followings
# ===========================================================================

class TestGetFollowings:
    def test_retrieves_followings(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_following.return_value = {"users": SAMPLE_USERS, "next_max_id": None}
        from instagram_private_api import Client as AppClient
        with patch.object(AppClient, "generate_uuid", return_value="fake-token"):
            og.get_followings()
        assert "follower1" in capsys.readouterr().out

    def test_dumps_followings_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        og.api.user_following.return_value = {"users": SAMPLE_USERS, "next_max_id": None}
        from instagram_private_api import Client as AppClient
        with patch.object(AppClient, "generate_uuid", return_value="fake-token"):
            og.get_followings()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_followings.json")))
        assert "followings" in data
        assert len(data["followings"]) == 2


# ===========================================================================
# Test: get_total_likes
# ===========================================================================

class TestGetTotalLikes:
    def test_computes_like_stats(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        og.get_total_likes()
        captured = capsys.readouterr()
        assert "175" in captured.out  # 100+50+25
        assert "3" in captured.out    # 3 posts

    def test_writes_likes_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        _setup_single_page_feed(og.api)
        og.get_total_likes()
        file_path = os.path.join(og.output_dir, "targetuser_likes.txt")
        assert os.path.isfile(file_path)
        assert "175" in open(file_path).read()

    def test_dumps_likes_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        og.get_total_likes()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_likes.json")))
        assert data["like_counter"] == 175
        assert data["posts"] == 3
        assert data["min"] == 25
        assert data["max"] == 100
        assert data["avg"] == 58  # int(175/3)


# ===========================================================================
# Test: get_media_type
# ===========================================================================

class TestGetMediaType:
    def test_counts_photos_and_videos(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        og.get_media_type()
        captured = capsys.readouterr()
        assert "2" in captured.out  # 2 photos
        assert "1" in captured.out  # 1 video

    def test_writes_mediatype_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        _setup_single_page_feed(og.api)
        og.get_media_type()
        file_path = os.path.join(og.output_dir, "targetuser_mediatype.txt")
        assert os.path.isfile(file_path)
        content = open(file_path).read()
        assert "2 photos" in content
        assert "1 videos" in content

    def test_dumps_mediatype_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        og.get_media_type()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_mediatype.json")))
        assert data["photos"] == 2
        assert data["videos"] == 1


# ===========================================================================
# Test: get_hashtags
# ===========================================================================

class TestGetHashtags:
    def test_extracts_hashtags(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        og.get_hashtags()
        captured = capsys.readouterr()
        assert "#travel" in captured.out
        assert "#fun" in captured.out

    def test_counts_hashtag_frequency(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        og.get_hashtags()
        captured = capsys.readouterr()
        assert "2. #travel" in captured.out  # in post_1 and post_2
        assert "1. #fun" in captured.out     # only in post_1

    def test_dumps_hashtags_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        og.get_hashtags()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_hashtags.json")))
        assert "hashtags" in data
        assert "#travel" in data["hashtags"]
        assert "#fun" in data["hashtags"]


# ===========================================================================
# Test: get_people_who_commented
# ===========================================================================

class TestGetPeopleWhoCommented:
    def test_aggregates_commenters(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_people_who_commented()
        captured = capsys.readouterr()
        assert "commenter1" in captured.out
        assert "commenter2" in captured.out

    def test_writes_people_who_commented_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_people_who_commented()
        assert os.path.isfile(os.path.join(og.output_dir, "targetuser_users_who_commented.txt"))

    def test_dumps_people_who_commented_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_people_who_commented()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_users_who_commented.json")))
        assert "users_who_commented" in data


# ===========================================================================
# Test: get_comments (same logic as get_people_who_commented)
# ===========================================================================

class TestGetComments:
    def test_aggregates_commenters(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_comments()
        captured = capsys.readouterr()
        assert "commenter1" in captured.out

    def test_dumps_comments_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        _setup_single_page_feed(og.api)
        _setup_single_page_comments(og.api)
        og.get_comments()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_users_who_commented.json")))
        assert "users_who_commented" in data


# ===========================================================================
# Test: get_photo_description
# ===========================================================================

class TestGetPhotoDescription:
    def test_extracts_descriptions(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {
            "items": [
                {"id": "p1", "accessibility_caption": "A sunset photo", "caption": {"text": "text"}},
                {"id": "p2", "accessibility_caption": None, "caption": {"text": "My vacation"}},
                {"id": "p3", "caption": None},
            ],
            "next_max_id": None,
        }
        og.get_photo_description()
        captured = capsys.readouterr()
        assert "A sunset photo" in captured.out
        assert "My vacation" in captured.out

    def test_writes_description_file(self, tmp_path):
        og = _make_osintgram(tmp_path, write_file=True)
        og.api.user_feed.return_value = {
            "items": [{"id": "p1", "accessibility_caption": "Test desc", "caption": {"text": "t"}}],
            "next_max_id": None,
        }
        og.get_photo_description()
        assert os.path.isfile(os.path.join(og.output_dir, "targetuser_photodes.txt"))

    def test_dumps_descriptions_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        og.api.user_feed.return_value = {
            "items": [{"id": "p1", "accessibility_caption": "Test desc", "caption": {"text": "t"}}],
            "next_max_id": None,
        }
        og.get_photo_description()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_descriptions.json")))
        assert data["descriptions"][0]["description"] == "Test desc"


# ===========================================================================
# Test: get_people_tagged_by_user
# ===========================================================================

class TestGetPeopleTaggedByUser:
    def test_extracts_tagged_users(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {
            "items": [
                {
                    "id": "p1",
                    "usertags": {"in": [
                        {"user": {"pk": 501, "username": "tagged1", "full_name": "Tagged One"}},
                        {"user": {"pk": 502, "username": "tagged2", "full_name": "Tagged Two"}},
                    ]},
                },
                {
                    "id": "p2",
                    "usertags": {"in": [
                        {"user": {"pk": 501, "username": "tagged1", "full_name": "Tagged One"}},
                    ]},
                },
                {"id": "p3"},
            ],
            "next_max_id": None,
        }
        og.get_people_tagged_by_user()
        captured = capsys.readouterr()
        assert "tagged1" in captured.out
        assert "tagged2" in captured.out

    def test_dumps_tagged_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        og.api.user_feed.return_value = {
            "items": [
                {
                    "id": "p1",
                    "usertags": {"in": [
                        {"user": {"pk": 501, "username": "tagged1", "full_name": "Tagged One"}},
                    ]},
                },
            ],
            "next_max_id": None,
        }
        og.get_people_tagged_by_user()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_tagged.json")))
        assert data["tagged"][0]["username"] == "tagged1"


# ===========================================================================
# Test: get_user_info
# ===========================================================================

class TestGetUserInfo:
    def _call_api_response(self):
        return {
            "user_detail": {
                "user": {
                    "pk": 12345,
                    "full_name": "Target User",
                    "biography": "A test bio",
                    "follower_count": 1000,
                    "following_count": 500,
                    "is_business": False,
                    "is_verified": True,
                    "hd_profile_pic_url_info": {"url": "http://example.com/pic.jpg"},
                }
            }
        }

    def test_prints_user_info(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api._call_api.return_value = self._call_api_response()
        og.get_user_info()
        captured = capsys.readouterr()
        assert "12345" in captured.out
        assert "Target User" in captured.out
        assert "A test bio" in captured.out

    def test_dumps_user_info_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        og.api._call_api.return_value = self._call_api_response()
        og.get_user_info()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_info.json")))
        assert data["id"] == 12345
        assert data["full_name"] == "Target User"


# ===========================================================================
# Test: get_user_stories
# ===========================================================================

class TestGetUserStories:
    @patch("urllib.request.urlretrieve")
    def test_downloads_stories(self, mock_urlretrieve, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_reel_media.return_value = {
            "items": [
                {"id": "s1", "media_type": 1,
                 "image_versions2": {"candidates": [{"url": "http://example.com/s1.jpg"}]}},
                {"id": "s2", "media_type": 2,
                 "video_versions": [{"url": "http://example.com/s2.mp4"}]},
            ],
            "media_count": 2,
        }
        og.get_user_stories()
        assert mock_urlretrieve.call_count == 2
        assert "2" in capsys.readouterr().out

    @patch("urllib.request.urlretrieve")
    def test_handles_no_stories(self, mock_urlretrieve, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_reel_media.return_value = {"items": None, "media_count": 0}
        og.get_user_stories()
        mock_urlretrieve.assert_not_called()
        assert "No results" in capsys.readouterr().out


# ===========================================================================
# Test: get_user_photo
# ===========================================================================

class TestGetUserPhoto:
    @patch("urllib.request.urlretrieve")
    def test_downloads_photos(self, mock_urlretrieve, tmp_path):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {
            "items": [
                {"id": "p1", "image_versions2": {"candidates": [{"url": "http://example.com/p1.jpg"}]}},
                {"id": "p2", "image_versions2": {"candidates": [{"url": "http://example.com/p2.jpg"}]}},
            ],
            "next_max_id": None,
        }
        og.get_user_photo()
        assert mock_urlretrieve.call_count == 2

    @patch("urllib.request.urlretrieve")
    def test_handles_carousel_media(self, mock_urlretrieve, tmp_path):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {
            "items": [
                {
                    "id": "carousel_1",
                    "carousel_media": [
                        {"id": "cm1", "image_versions2": {"candidates": [{"url": "http://example.com/c1.jpg"}]}},
                        {"id": "cm2", "image_versions2": {"candidates": [{"url": "http://example.com/c2.jpg"}]}},
                    ],
                },
            ],
            "next_max_id": None,
        }
        og.get_user_photo()
        assert mock_urlretrieve.call_count == 2


# ===========================================================================
# Test: get_user_propic
# ===========================================================================

class TestGetUserPropic:
    @patch("urllib.request.urlretrieve")
    def test_downloads_profile_pic(self, mock_urlretrieve, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api._call_api.return_value = {
            "user_detail": {
                "user": {"hd_profile_pic_url_info": {"url": "http://example.com/hd.jpg"}}
            }
        }
        og.get_user_propic()
        mock_urlretrieve.assert_called_once()
        assert "propic saved" in capsys.readouterr().out

    @patch("urllib.request.urlretrieve")
    def test_falls_back_to_versions(self, mock_urlretrieve, tmp_path):
        og = _make_osintgram(tmp_path)
        og.api._call_api.return_value = {
            "user_detail": {
                "user": {
                    "hd_profile_pic_versions": [
                        {"url": "http://example.com/low.jpg"},
                        {"url": "http://example.com/high.jpg"},
                    ]
                }
            }
        }
        og.get_user_propic()
        args = mock_urlretrieve.call_args[0]
        assert "high.jpg" in args[0]


# ===========================================================================
# Test: get_people_who_tagged
# ===========================================================================

class TestGetPeopleWhoTagged:
    def test_retrieves_user_tags(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.usertag_feed.return_value = {
            "items": [
                {"user": {"pk": 601, "username": "tagger1", "full_name": "Tagger One"}},
                {"user": {"pk": 602, "username": "tagger2", "full_name": "Tagger Two"}},
                {"user": {"pk": 601, "username": "tagger1", "full_name": "Tagger One"}},
            ],
            "next_max_id": None,
        }
        og.get_people_who_tagged()
        captured = capsys.readouterr()
        assert "tagger1" in captured.out
        assert "tagger2" in captured.out

    def test_dumps_tagged_json(self, tmp_path):
        og = _make_osintgram(tmp_path, json_dump=True)
        og.api.usertag_feed.return_value = {
            "items": [
                {"user": {"pk": 601, "username": "tagger1", "full_name": "Tagger One"}},
            ],
            "next_max_id": None,
        }
        og.get_people_who_tagged()
        data = json.load(open(os.path.join(og.output_dir, "targetuser_users_who_tagged.json")))
        assert "users_who_tagged" in data


# ===========================================================================
# Test: Feed pagination
# ===========================================================================

class TestFeedPagination:
    def test_paginates_feed(self, tmp_path):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.side_effect = [
            {"items": [SAMPLE_FEED_ITEMS[0]], "next_max_id": "page2"},
            {"items": [SAMPLE_FEED_ITEMS[1]], "next_max_id": "page3"},
            {"items": [SAMPLE_FEED_ITEMS[2]], "next_max_id": None},
        ]
        result = og.__get_feed__()
        assert len(result) == 3
        assert og.api.user_feed.call_count == 3


# ===========================================================================
# Test: Comment pagination
# ===========================================================================

class TestCommentPagination:
    def test_paginates_comments(self, tmp_path):
        og = _make_osintgram(tmp_path)
        og.api.media_comments.side_effect = [
            {"comments": [SAMPLE_COMMENTS[0]], "next_max_id": "page2"},
            {"comments": [SAMPLE_COMMENTS[1]], "next_max_id": None},
        ]
        result = og.__get_comments__("post_1")
        assert len(result) == 2
        assert og.api.media_comments.call_count == 2


# ===========================================================================
# Test: Private profile guard
# ===========================================================================

class TestPrivateProfileGuard:
    def test_private_profile_blocks_captions(self, tmp_path):
        og = _make_osintgram(tmp_path)
        og.is_private = True
        og.following = False
        with patch("builtins.input", return_value="n"):
            og.get_captions()
        og.api.user_feed.assert_not_called()

    def test_private_profile_blocks_followers(self, tmp_path):
        og = _make_osintgram(tmp_path)
        og.is_private = True
        og.following = False
        with patch("builtins.input", return_value="n"):
            og.get_followers()
        og.api.user_followers.assert_not_called()

    def test_public_profile_allows_access(self, tmp_path):
        og = _make_osintgram(tmp_path)
        og.is_private = False
        _setup_single_page_feed(og.api)
        og.get_captions()
        og.api.user_feed.assert_called()


# ===========================================================================
# Test: _validate_username
# ===========================================================================

class TestValidateUsername:
    def test_valid_username_passes(self):
        from src.Osintgram import Osintgram
        Osintgram._validate_username("john_doe.123")

    def test_empty_username_exits(self):
        from src.Osintgram import Osintgram
        with pytest.raises(SystemExit):
            Osintgram._validate_username("")

    def test_none_username_exits(self):
        from src.Osintgram import Osintgram
        with pytest.raises(SystemExit):
            Osintgram._validate_username(None)

    def test_invalid_chars_exits(self):
        from src.Osintgram import Osintgram
        with pytest.raises(SystemExit):
            Osintgram._validate_username("user@name")

    def test_too_long_exits(self):
        from src.Osintgram import Osintgram
        with pytest.raises(SystemExit):
            Osintgram._validate_username("a" * 31)


# ===========================================================================
# Test: Empty results handling
# ===========================================================================

class TestEmptyResults:
    def test_no_captions_prints_no_results(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {"items": [], "next_max_id": None}
        og.get_captions()
        assert "No results" in capsys.readouterr().out

    def test_no_hashtags_prints_no_results(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {"items": [{"caption": None}], "next_max_id": None}
        og.get_hashtags()
        assert "No results" in capsys.readouterr().out

    def test_no_media_type_prints_no_results(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {"items": [], "next_max_id": None}
        og.get_media_type()
        assert "No results" in capsys.readouterr().out

    def test_no_tagged_prints_no_results(self, tmp_path, capsys):
        og = _make_osintgram(tmp_path)
        og.api.user_feed.return_value = {"items": [], "next_max_id": None}
        og.get_people_tagged_by_user()
        assert "No results" in capsys.readouterr().out
