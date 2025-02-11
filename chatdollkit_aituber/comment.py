import multiprocessing
from typing import Callable, Optional
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent,GiftEvent,JoinEvent,LikeEvent
from TikTokLive.client.logger import LogLevel
from .utility import LikeTracker

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
        self.like_count = LikeTracker()

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

        if(event.user.member_level or event.user.member_rank):
            self.client.logger.info(f"挨拶対象（友達）：{event.user.follow_info.follow_status}-{event.user.member_level}-{event.user.member_rank}:{event.user.nickname}")
            author = Author(name=f"{event.user.nickname}")
            c = Comment(author=author, message="ただいま！")
            self.process_comment(c)
        elif(event.user.gifter_level is not None and event.user.gifter_level > 10):
            self.client.logger.info(f"挨拶対象（ギフレベ高）　：{event.user.gifter_level}:{event.user.nickname}")
            # ギフレベ高い人に挨拶
            author = Author(name=event.user.nickname)
            c = Comment(author=author, message="お邪魔します")
            self.process_comment(c)
        elif(event.user.follow_info.follow_status > 0):
            # self.client.logger.info(f"挨拶対象（知り合い）：{event.user.follow_info.follow_status}-{event.user.member_level}-{event.user.member_rank}:{event.user.nickname}")
            # 知り合いに挨拶
            author = Author(name=event.user.nickname)
            c = Comment(author=author, message="こんにちは")
            # self.process_comment(c)
        else:
            self.client.logger.info(f"Join -> {event.user.pay_grade.level}-{event.user.gifter_level}-{event.user.follow_info.follow_status}:{event.user.nickname}")
            # print(f"挨拶対象外：{event.user.member_level,event.user.is_follower,event.user.is_following,event.user.anchor_level.level,event.user.follow_status}:{event.user.nickname}")

    async def on_like(self,event: LikeEvent) -> None:
        # print(f"{event.user.unique_id, event.user.nickname, event.count}")
        self.like_count.add_like(user_id=event.user.unique_id, display_name=event.user.nickname, like_count=event.count)
        if(self.like_count.get_likes(event.user.unique_id) is not None):
            current_likes = self.like_count.get_likes(event.user.unique_id)[1]
            if(current_likes > 100):
                self.client.logger.info(f"Like -> {current_likes}:{self.like_count.get_likes(event.user.unique_id)[0]}")
                author = Author(name=self.like_count.get_likes(event.user.unique_id)[0])
                message = f"ライブいいねを{current_likes}回したよ！"
                # print(f"{message}:{self.like_count.get_likes(event.user.unique_id)[0]}")
                c = Comment(author=author, message=message)

                self.like_count.add_like(user_id=event.user.unique_id, display_name=event.user.nickname, like_count=-current_likes)
                self.process_comment(c)

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
        self.client.add_listener(LikeEvent, self.on_like)

        self.client.logger.setLevel(LogLevel.INFO.value)

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
