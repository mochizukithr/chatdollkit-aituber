class LikeTracker:
    def __init__(self):
        self.user_data = {}  # ユーザーID: (表示名, Like数)

    def add_like(self, user_id: str, display_name: str, like_count: int):
        """ユーザーのLike数を加算し、表示名も管理"""
        if user_id in self.user_data:
            current_display_name, current_likes = self.user_data[user_id]
            self.user_data[user_id] = (display_name, current_likes + like_count)
        else:
            self.user_data[user_id] = (display_name, like_count)

        # print(f"{display_name}（{user_id}）の現在のLike数: {self.user_data[user_id][1]}")

    def get_likes(self, user_id: str):
        """指定したユーザーIDの表示名と合計Like数を取得"""
        if user_id in self.user_data:
            return self.user_data[user_id]  # (表示名, Like数)
        else:
            return None  # ユーザーが見つからない場合

# 使用例
# like_tracker = LikeTracker()

# like_tracker.add_like("user_123", "Alice", 5)  
# like_tracker.add_like("user_456", "Bob", 3)  
# like_tracker.add_like("user_123", "Alice", 2)  

# # 特定のユーザーのデータを取得
# print(like_tracker.get_likes("user_123"))  # ('Alice', 7)
# print(like_tracker.get_likes("user_456"))  # ('Bob', 3)
# print(like_tracker.get_likes("user_999"))  # None（存在しないユーザー）
