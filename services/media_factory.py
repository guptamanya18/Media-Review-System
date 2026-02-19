# app/models.py or app/services/media_factory.py

class Media:
    def __init__(self, media_id, title, genre):
        self.media_id = media_id
        self.title = title
        self.genre = genre

    def display_info(self):
        return f"{self.title} ({self.genre})"

class Movie(Media):
    def __init__(self, media_id, title, genre, rating=None):
        super().__init__(media_id, title, genre)
        self.rating = rating  # Movie-specific attribute

class WebShow(Media):
    def __init__(self, media_id, title, genre, episodes=0):
        super().__init__(media_id, title, genre)
        self.episodes = episodes  # WebShow-specific attribute

class Song(Media):
    def __init__(self, media_id, title, genre, popularity=0):
        super().__init__(media_id, title, genre)
        self.popularity = popularity  # Song-specific attribute

        
class MediaFactory:
    @staticmethod
    def create_media(media_type, media_id, title, genre, **kwargs):
        if media_type.lower() == 'movie':
            return Movie(media_id, title, genre, kwargs.get('rating'))
        elif media_type.lower() == 'webshow':
            return WebShow(media_id, title, genre, kwargs.get('episodes', 0))
        elif media_type.lower() == 'song':
            return Song(media_id, title, genre, kwargs.get('popularity', 0))
        else:
            raise ValueError(f"Unknown media type: {media_type}")
