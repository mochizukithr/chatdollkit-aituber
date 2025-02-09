import multiprocessing
from typing import Callable, Optional
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent,GiftEvent,JoinEvent
from TikTokLive.client.logger import LogLevel

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
        # print(f"{event.user.nickname} -> {event.comment}")
        if not event.comment.startswith('@'):
          author = Author(name=event.user.nickname)
          c = Comment(author=author, message=event.comment)
          self.process_comment(c)
    async def on_gift(self, event: GiftEvent) -> None:
        print(f"{event.user.nickname} -> {event.comment}")
        if not event.comment.startswith('@'):
          author = Author(name=event.user.nickname)
          c = Comment(author=author, message=event.comment)
          self.process_comment(c)

    async def on_gift(self,event: GiftEvent):
        # Streakable gift & streak is over
        if event.gift.streakable and not event.streaking:
            # print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")
            author = Author(name=event.user.nickname)
            message = f"!gift {event.gift.name}を{event.repeat_count}個プレゼントします"
            print(message)
            c = Comment(author=author, message=message)
            self.process_comment(c)

        # Non-streakable gift
        elif not event.gift.streakable:
            # print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
            author = Author(name=event.user.nickname)
            message = f"!gift {event.gift.name}を{event.repeat_count}個プレゼントします"
            print(message)
            c = Comment(author=author, message=message)
            self.process_comment(c)


    async def on_join(self, event: JoinEvent) -> None:
        # print(f"Join -> {event.user}")
        if(event.user.member_level is not None or event.user.is_follower or event.user.is_following or event.user.anchor_level.level > 5):
            print(f"挨拶対象　：{event.user.member_level,event.user.is_follower,event.user.is_following,event.user.anchor_level.level,event.user.follow_status}:{event.user.nickname}")
            # フォロワーやメンレベ、ギフレベ高い人に挨拶
            author = Author(name=event.user.nickname)
            c = Comment(author=author, message="こんにちは")
            # self.process_comment(c)
        else:
            print(f"挨拶対象外：{event.user.member_level,event.user.is_follower,event.user.is_following,event.user.anchor_level.level,event.user.follow_status}:{event.user.nickname}")

    def start_monitoring(self, video_id,session_id):
        # Create the client
        print(f"start_monitoring {video_id}")
        self.client: TikTokLiveClient = TikTokLiveClient(unique_id=video_id)

        print(f"session_id: {session_id}")
        self.client.web.set_session_id(session_id)

        self.client.add_listener(ConnectEvent, self.on_connect)
        self.client.add_listener(CommentEvent, self.on_comment)
        self.client.add_listener(GiftEvent, self.on_gift)
        self.client.add_listener(JoinEvent, self.on_join)

        # self.client.logger.setLevel(LogLevel.DEBUG.value)

        self.client.run()

class CommentMonitorManager:
    def __init__(self, process_comment: Callable):
        self.comment_monitor = CommentMonitor(process_comment)
        self.process: Optional[multiprocessing.Process] = None
        self.video_id: Optional[str] = None

    def run_monitor(self, video_id: str,session_id:str):
        self.comment_monitor.start_monitoring(video_id,session_id)

    def start(self, video_id: str,session_id:str) -> bool:
        if self.process and self.process.is_alive():
            return False

        self.process = multiprocessing.Process(
            target=self.run_monitor,
            args=(video_id,session_id)
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
