from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Music:
    music_name: str 
    duration: int 


class Playlist: 
    def __init__(self) -> None:
        self._playlist: list[Music] = []
    
    def add_song(self, name: str, duration: int) -> None: 
        if name and duration: 
            song = Music(name, duration)
            self._playlist.append(song)
    
    def remove_song(self, name) -> None: 
        for i in self._playlist: 
            if name == i.music_name: 
                self._playlist.remove(i)
                break
                
    
    def total_duration(self): 
        return sum(i.duration for i in self._playlist)

    def __iter__(self): 
        for song in self._playlist:
            yield (song.music_name, song.duration) 
    def __len__(self): 
        return len(self._playlist)

if __name__ == '__main__': 
    playlist = Playlist()
    playlist.add_song('Song 1', 200)
    playlist.add_song('Song 2', 300)
    playlist.add_song('Song 3', 600)
    playlist.add_song('Song 3', 600)
    print(len(playlist))
    print(playlist.total_duration())
    playlist.remove_song('Song 3')
    playlist.remove_song('Song 67')
    print(playlist.total_duration())

    for i in playlist: 
        print(i)
