import requests
import re
import argparse

def get_user_info(identifier, by_id=False):
    if by_id:
        url = f"https://www.tiktok.com/@{identifier}"
    else:
        if identifier.startswith('@'):
            identifier = identifier[1:]
        url = f"https://www.tiktok.com/@{identifier}"

    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"Failed to fetch data, status code: {response.status_code}"}

    html_content = response.text

    patterns = {
        "user_id": r'"webapp.user-detail":{"userInfo":{"user":{"id":"(\d+)"',
        "unique_id": r'"uniqueId":"(.*?)"',
        "nickname": r'"nickname":"(.*?)"',
        "followers": r'"followerCount":(\d+)',
        "following": r'"followingCount":(\d+)',
        "likes": r'"heartCount":(\d+)',
        "videos": r'"videoCount":(\d+)',
        "signature": r'"signature":"(.*?)"',
        "verified": r'"verified":(true|false)',
        "secUid": r'"secUid":"(.*?)"',
        "commentSetting": r'"commentSetting":(\d+)',
        "privateAccount": r'"privateAccount":(true|false)',
        "region": r'"region":"(.*?)"',
        "heart": r'"heart":(\d+)',
        "diggCount": r'"diggCount":(\d+)',
        "friendCount": r'"friendCount":(\d+)',
        "profile_pic": r'"avatarLarger":"(.*?)"',
    }

    user_data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, html_content)
        user_data[key] = match.group(1).replace('\\u002F', '/') if match else None

    # Convert some fields to integers
    int_fields = ["followers", "following", "likes", "videos", "heart", "diggCount", "friendCount", "commentSetting"]
    for field in int_fields:
        if user_data[field] is not None:
            user_data[field] = int(user_data[field])

    # Convert boolean fields
    bool_fields = ["verified", "privateAccount"]
    for field in bool_fields:
        if user_data[field] is not None:
            user_data[field] = user_data[field] == "true"

    # Download profile picture
    # if user_data["profile_pic"]:
    #     profile_pic_response = requests.get(user_data["profile_pic"])
    #     if profile_pic_response.status_code == 200:
    #         with open(f"{user_data['unique_id']}_profile_pic.jpg", "wb") as file:
    #             file.write(profile_pic_response.content)
    #         user_data["profile_pic_downloaded"] = f"{user_data['unique_id']}_profile_pic.jpg"
    #     else:
    #         user_data["profile_pic_downloaded"] = "Failed to download"

    return user_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get TikTok user information")
    parser.add_argument("identifier", type=str, help="TikTok username or user ID")
    parser.add_argument("--by_id", action="store_true", help="Indicates if the provided identifier is a user ID")
    args = parser.parse_args()
    
    data = get_user_info(args.identifier, args.by_id)
    print(data)