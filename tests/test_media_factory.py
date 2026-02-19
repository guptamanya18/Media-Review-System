import unittest
from services.media_factory import MediaFactory, Movie, WebShow, Song


class TestMediaFactory(unittest.TestCase):

    def test_create_movie(self):
        movie = MediaFactory.create_media("movie", 1, "Inception", "Sci-Fi", rating=9)
        self.assertIsInstance(movie, Movie)
        self.assertEqual(movie.title, "Inception")
        self.assertEqual(movie.rating, 9)

    def test_create_webshow(self):
        ws = MediaFactory.create_media("webshow", 2, "Stranger Things", "Thriller", episodes=40)
        self.assertIsInstance(ws, WebShow)
        self.assertEqual(ws.episodes, 40)

    def test_create_song(self):
        song = MediaFactory.create_media("song", 3, "Shape of You", "Pop", popularity=95)
        self.assertIsInstance(song, Song)
        self.assertEqual(song.popularity, 95)

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            MediaFactory.create_media("podcast", 4, "Test", "Genre")

    def test_movie_display_info(self):
        movie = MediaFactory.create_media("movie", 5, "Dune", "Sci-Fi")
        self.assertIn("Dune", movie.display_info())

    def test_webshow_default_episodes(self):
        ws = MediaFactory.create_media("webshow", 6, "Friends", "Comedy")
        self.assertEqual(ws.episodes, 0)

    def test_song_default_popularity(self):
        song = MediaFactory.create_media("song", 7, "Blinding Lights", "Pop")
        self.assertEqual(song.popularity, 0)

    def test_case_insensitive_type(self):
        movie = MediaFactory.create_media("MOVIE", 8, "Matrix", "Sci-Fi")
        self.assertIsInstance(movie, Movie)


if __name__ == "__main__":
    unittest.main()
