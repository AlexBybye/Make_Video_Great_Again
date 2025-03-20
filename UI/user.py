class User:
    def __init__(self, uid, gender, age):
        self.uid = uid
        self.gender = gender
        self.age = age

    def interact_with_video(self, video, action):
        if action == "like":
            video.like()
        elif action == "comment":
            video.comment()
        elif action == "share":
            video.share()
        else:
            raise ValueError("Invalid action")