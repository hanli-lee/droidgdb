#!/usr/bin/python                                                                                                                                                                       
# -*- coding: utf-8 -*- 
# author: hanli


class AndroidRuntime:
    __ANDROID_VERSION = 0

    @classmethod
    def getAndroidVersion(cls):
        return int(cls.__ANDROID_VERSION)

    @classmethod
    def setAndroidVersion(cls, version):
        cls.__ANDROID_VERSION = version
