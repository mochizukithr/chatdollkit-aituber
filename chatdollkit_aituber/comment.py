import multiprocessing
from typing import Callable, Optional
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

class Author:
    def __init__(self, name: str):
        self.name = name

class Comment:
    def __init__(self, author: Author, message: str):
        self.author = author
        self.message = message

class CommentMonitor:
    def __init__(self, process_comment: Callable):
        self.process_comment = process_comment

    async def on_connect(self, event: ConnectEvent) -> None:
        print(f"Connected to @{event.unique_id} (Room ID: {self.client.room_id}")
    async def on_comment(self, event: CommentEvent) -> None:
        print(f"{event.user.nickname} -> {event.comment}")
        if not event.comment.startswith('@'):
          author = Author(name=event.user.nickname)
          c = Comment(author=author, message=event.comment)
          self.process_comment(c)
    def start_monitoring(self, video_id):
        # Create the client
        self.client: TikTokLiveClient = TikTokLiveClient(unique_id=video_id)
        print(f"start_monitoring {video_id}")

        self.client.add_listener(ConnectEvent, self.on_connect)
        self.client.add_listener(CommentEvent, self.on_comment)
        self.client.run()

class CommentMonitorManager:
    def __init__(self, process_comment: Callable):
        self.comment_monitor = CommentMonitor(process_comment)
        self.process: Optional[multiprocessing.Process] = None
        self.video_id: Optional[str] = None

    def run_monitor(self, video_id: str):
        self.comment_monitor.start_monitoring(video_id)

    def start(self, video_id: str) -> bool:
        if self.process and self.process.is_alive():
            return False

        self.process = multiprocessing.Process(
            target=self.run_monitor,
            args=(video_id,)
        )
        self.process.start()
        self.video_id = video_id
        return True

    def stop(self) -> bool:
        if not self.process or not self.process.is_alive():
            return False

        self.process.terminate()
        self.process.join()
        self.video_id = None
        return True

    def get_status(self):
        is_running = bool(self.process and self.process.is_alive())
        return is_running, self.video_id if is_running else None
