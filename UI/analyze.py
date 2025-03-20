import pickle

def load_data():
    with open("videos.csv", "rb") as f:
        videos = pickle.load(f)
    with open("users.csv", "rb") as f:
        users = pickle.load(f)
    return videos, users

def analyze_videos(videos):
    total_likes = sum(video.likes for video in videos)
    total_comments = sum(video.comments for video in videos)
    total_shares = sum(video.shares for video in videos)
    print(f"Total Likes: {total_likes}")
    print(f"Total Comments: {total_comments}")
    print(f"Total Shares: {total_shares}")

def analyze_users(users):
    male_count = sum(1 for user in users if user.gender == "male")
    female_count = sum(1 for user in users if user.gender == "female")
    print(f"Male Users: {male_count}")
    print(f"Female Users: {female_count}")

if __name__ == "__main__":
    videos, users = load_data()
    analyze_videos(videos)
    analyze_users(users)