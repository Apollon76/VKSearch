import urllib.request
import json


class User:
    def __init__(self, data):
        user_id = data['id']
        self.user_id = user_id
        self.name = data['first_name']
        self.surname = data['last_name']
        if 'photo_50' in data:
            self.link_to_photo = data['photo_50']
        else:
            self.link_to_photo = 'https://new.vk.com/images/deactivated_hid_50.gif'
        if 'photo_400_orig' in data:
            self.link_to_original_photo = data['photo_400_orig']
        else:
            self.link_to_original_photo = 'https://new.vk.com/images/deactivated_hid_400.gif'

    @classmethod
    def get_by_id(cls, user_id: str):
        with urllib.request.urlopen('https://api.vk.com/method/users.get?user_ids={}&fields=nickname,city,sex,photo_50,photo_400_orig&v=5.52'.format(user_id)) as stream:
            data = stream.read().decode('utf-8')
        data = json.loads(data)
        if 'error' in data:
            raise ValueError('No such user id: {}'.format(user_id))
        try:
            data = data['response'][0]
        except IndexError:
            raise ValueError(data)
        return cls(data)

    def get_friends(self):
        with urllib.request.urlopen(
                'https://api.vk.com/method/friends.get?user_id={}&order=hints&fields=nickname,city,sex,photo_50,photo_400_orig&v=5.52'
                        .format(self.user_id)
        ) as stream:
            data = stream.read().decode('utf-8')
        data = json.loads(data)['response']['items']
        friend_list = map(lambda x: User(x), data)
        return friend_list

    def get_photo(self):
        return self.link_to_photo

    def get_original_photo(self):
        return self.link_to_original_photo

    def __str__(self):
        return self.name + ' ' + self.surname

    def __eq__(self, other):
        return isinstance(other, User) and self.user_id == other.user_id

    def __hash__(self):
        return hash(self.user_id)

    def __lt__(self, other):
        if not isinstance(other, User):
            raise ValueError
        return self.user_id < other.user_id

    def review(self):
        friends = self.get_friends()
        text = str(self) + '\n\n'
        men = 0
        women = 0
        text += '{} друзей\n\n'.format(str(len(friends)))
        for friend in friends:
            if 'city' in friend:
                text += '{} {}\nг. {}\n\n'.format(friend['first_name'], friend['last_name'], friend['city']['title'])
            else:
                text += '{} {}\nГород скрыт\n\n'.format(friend['first_name'], friend['last_name'])
            if 'sex' in friend:
                if friend['sex'] == 2:
                    men += 1
                else:
                    women += 1
        text += '{}% мужчин, {}% женщин'.format(int(men / (men + women) * 100), int(women / (men + women) * 100))
        return text


class Image:
    def __init__(self, data):
        self.link = None
        for i in data:
            if i.startswith('photo_'):
                self.link = data[i]
                break
        if self.link is None:
            raise ValueError

    def get_link(self):
        return self.link

