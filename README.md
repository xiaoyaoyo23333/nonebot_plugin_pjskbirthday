# nonebot_plugin_pjskbirthday
一个偏向个人用的nb2生日推送插件pjsk角色版

安装步骤：
使用nb-cli创建新的插件（插件名：pjskbirthday）
下载/复制仓库的init.py和config.py 到新的插件目录/pjskbirthday下
运行一次nonebot2,使其自动创建/data/pjskbirthday
下载config.zip，解压到/data/pjskbirthday
可能需要再次启动nonebot2才能正确加载配置文件

使用方式：
在配置文件“characters.json”（/data/pjskbirthday）里配置群聊白名单、不需要推送的角色（例子： "comment": "不需要推送初音未来",），图片文件名称等

角色生日当天0时0分自动向白名单群聊推送该角色生日

指令：
/pjsk生日列表
/pjsk 测试角色 角色名
