# coding=utf-8
"""
维护全局变量：全局用户列表、全局视频列表
"""

import InitWeightMatrix


def help_find(uid: int, global_list, bToDelete: bool):  # bToDelete 指明在遍历时是否删除该元素，用于提高删除效率
    for item in global_list:
        if uid == item.uid:
            if bToDelete:
                global_list.remove(item)
            return True
    return False


class GlobalVariable:
    def __init__(self):
        self.GlobalVideoList = []
        self.GlobalUserList = []
        self.InitWeight = InitWeightMatrix.InitWeight()  # 初始权重具有全局性

    def GetTotalUserCount(self):
        return len(self.GlobalUserList)

    def GetTotalVideoCount(self):
        return len(self.GlobalVideoList)

    def add_video_to_list(self, video):
        if not help_find(video.uid, self.GlobalVideoList, False):
            self.GlobalVideoList.append(video)

    def add_user_to_list(self, user):
        if not help_find(user.uid, self.GlobalUserList, False):
            self.GlobalUserList.append(user)

    def del_video_from_list(self, video):
        if not help_find(video.uid, self.GlobalVideoList, True):
            return True
        else:
            return False

    def del_user_from_list(self, user):
        if not help_find(user.uid, self.GlobalUserList, True):
            return True
        else:
            return False

    @staticmethod
    def set_video_hot(video, bSet=True):  # 设置视频视为为热，默认调用设为热
        if bSet:
            video.hot = True
        else:
            video.hot = False

    def get_video_list_by_category(self, category):
        result = []
        for video in self.GlobalVideoList:
            if video.category == category:
                result.append(video)
        return result

    def get_user_list_by_attr(self, work_phase, gender, job):
        result = []
        for user in self.GlobalUserList:
            if user.work_phase == work_phase and user.gender == gender and user.job == job:
                result.append(user)
        return result


global_obj = GlobalVariable()  # 全局变量
refresh_frequency = 100  # 用户刷n条视频后重新计算权重
hot_add_weight_percent: float = 0.1  # 对于被设置为“热”的视频，以百分比方式增加权重，如原来权重为3，则增加为3*(1+0.1)=3.3
