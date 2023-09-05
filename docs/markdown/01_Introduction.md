# 简介

<div style="position: fixed; top: 90%; left: 90%">
<a href="#目录" style="text-decoration: none; display: none">返回目录</a>
</div>

NSUKit为一套用于各种射频/数字组件的SDK。支持c++、python等编程语言，此接口完成了 **主机对板级交互的层级抽象** ，目标是 **分割上层应用程序和多种多样的板级IO接口** ，可以实现 **一次开发、多板卡兼容** 。

_本文档为NSUKit的python语言版本的使用文档。_

<center>![](main_framework.png)</center>
<center>NSUKit基本框架</center>

---
## 用户手册
1. [快速开始](02_Quickstart.md)：接口功能详细介绍、安装与基本使用
2. [进阶使用](03_Professional.md)：板卡模拟功能与异步数据流上行接口
3. [ICD指令](04_ICDScheme.md)：介绍了一种主机与板上/片上处理核间的指令协议，nsukit内置支持
4. [NSUKit类](#nsukit.base_kit.NSUKit)：nsukit对外提供的接口类NSUKit的文档

---
## 应用示例
1. [使用NSUKit与NSUFDK交互](app/nsu_fdk.md)：提供了对于NSUFDK套件的应用示例，NSUFDK用户可以从此文档开始阅读(待完善)

---
