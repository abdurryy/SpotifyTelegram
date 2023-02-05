import pafy, wget, os
from youtubesearchpython import VideosSearch

class SpotifyDownload:
    def download(song):
        try:
            result = [video['link']
                    for video in VideosSearch(song, limit=1).result()['result']]
            final_result = result[0]
            url = pafy.new(final_result)
            media = url.getbestaudio()
            if os.path.isfile("songs/{}.mp3".format(media.title)) == False:
                wget.download(media.url, out="songs/{}.mp3".format(media.title))
            return "songs/{}.mp3".format(media.title)
        except:
            return SpotifyDownload.download(song)