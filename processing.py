from collections import defaultdict

from API import User


def merge_friends(user_ids: list) -> list:
    if len(user_ids) == 0:
        raise ValueError('List of users can not be empty')
    users_list = list(map(lambda x: User.get_by_id(x), user_ids))
    friend_lists = []
    for user in users_list:
        friend_lists.append(user.get_friends())
    union = defaultdict(int)
    for i in friend_lists:
        for user in i:
            union[user] += 1
    union = list(map(lambda x: (union[x], x), union))
    union.sort(reverse=True)
    return union


def test(ids: list):
    # ids = ['mr146', 'gardener_giraffe', 'ritashadrina', 'kungasc']
    union = merge_friends(ids)
    for i in union:
        print('{} {}'.format(i[1], i[0]))