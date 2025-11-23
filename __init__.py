import nonebot
from nonebot import get_driver, logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Bot, MessageSegment, Message
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
import asyncio

from .config import PjskBirthdayConfig, PluginConfig, CharacterConfig

__plugin_meta__ = PluginMetadata(
    name="PJSK生日推送",
    description="Project Sekai角色生日推送插件",
    usage="自动在角色生日当天发送祝福\n命令:\n- /pjsk生日列表 - 查看所有角色生日\n- /pjsk测试角色 [角色名] - 测试指定角色生日推送",
    type="application",
    homepage="",
    supported_adapters={"~onebot.v11"},
)

# 插件数据目录
DATA_DIR = Path("data/pjskbirthday")
IMAGES_DIR = DATA_DIR / "images"
CONFIG_FILE = DATA_DIR / "characters.json"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# 全局配置
plugin_config: PluginConfig = None
characters_config: Dict[str, CharacterConfig] = {}

def load_config():
    """加载配置文件"""
    global plugin_config, characters_config
    
    if not CONFIG_FILE.exists():
        logger.error(f"配置文件不存在: {CONFIG_FILE}")
        logger.info("请创建配置文件并添加角色信息")
        plugin_config = PluginConfig()
        characters_config = {}
        return
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        pjsk_config = PjskBirthdayConfig(**config_data)
        plugin_config = pjsk_config.plugin_config
        characters_config = pjsk_config.characters
        logger.info("PJSK生日插件配置加载成功")
        logger.info(f"白名单群组: {plugin_config.white_list_groups}")
        
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        plugin_config = PluginConfig()
        characters_config = {}

def get_today_birthday_characters() -> List[CharacterConfig]:
    """获取今天生日的角色"""
    today = datetime.now().strftime("%m-%d")
    birthday_characters = []
    
    for group_id, group_data in characters_config.items():
        if group_id == "plugin_config":
            continue
        
        for char_id, char_config in group_data.items():
            if char_id == "comment":
                continue
            
            if isinstance(char_config, dict) and char_config.get("birthday") == today:
                birthday_characters.append(CharacterConfig(**char_config))
    
    return birthday_characters

def get_character_by_name(character_name: str) -> CharacterConfig:
    """根据角色名获取角色配置"""
    for group_id, group_data in characters_config.items():
        if group_id == "plugin_config":
            continue
        
        for char_id, char_config in group_data.items():
            if char_id == "comment":
                continue
            
            if (isinstance(char_config, dict) and 
                char_config.get("name") == character_name):
                return CharacterConfig(**char_config)
    
    return None

def build_birthday_message(character: CharacterConfig, is_test: bool = False) -> Message:
    """构建生日消息"""
    image_path = IMAGES_DIR / character.image_file
    
    prefix = "[测试] " if is_test else ""
    
    if image_path.exists():
        with open(image_path, 'rb') as f:
            image_data = f.read()
        image_segment = MessageSegment.image(image_data)
    else:
        image_segment = MessageSegment.text("[图片文件不存在]")
        logger.warning(f"角色图片不存在: {image_path}")
    
    message = Message([
        MessageSegment.text(f"{prefix}🎉今天是 {character.name} 的生日！\n"),
        image_segment
    ])
    
    return message

async def send_birthday_notification(bot: Bot):
    """发送生日通知"""
    try:
        today_characters = get_today_birthday_characters()
        
        if not today_characters:
            logger.info("今天没有PJSK角色过生日")
            return
        
        for character in today_characters:
            message = build_birthday_message(character)
            
            if plugin_config.enable_group and plugin_config.white_list_groups:
                for group_id in plugin_config.white_list_groups:
                    try:
                        await bot.send_group_msg(group_id=group_id, message=message)
                        logger.info(f"已发送 {character.name} 生日祝福到群 {group_id}")
                        await asyncio.sleep(1)  # 避免发送过快
                    except Exception as e:
                        logger.error(f"发送到群 {group_id} 失败: {e}")
    
    except Exception as e:
        logger.error(f"发送PJSK生日通知时发生错误: {e}")

async def send_test_character(bot: Bot, character_name: str):
    """测试指定角色生日推送"""
    character = get_character_by_name(character_name)
    if not character:
        return False, f"未找到角色: {character_name}"
    
    message = build_birthday_message(character, is_test=True)
    
    success_count = 0
    total_count = 0
    
    if plugin_config.enable_group and plugin_config.white_list_groups:
        for group_id in plugin_config.white_list_groups:
            total_count += 1
            try:
                await bot.send_group_msg(group_id=group_id, message=message)
                logger.info(f"测试消息已发送 {character.name} 到群 {group_id}")
                success_count += 1
                await asyncio.sleep(1)  # 避免发送过快
            except Exception as e:
                logger.error(f"测试消息发送到群 {group_id} 失败: {e}")
    
    if success_count == 0:
        return False, f"角色 {character_name} 测试失败，无法发送到任何群组"
    else:
        return True, f"角色 {character_name} 测试完成，成功发送到 {success_count}/{total_count} 个群组"

async def pjsk_birthday_scheduler():
    """PJSK生日定时检查任务"""
    while True:
        now = datetime.now()
        # 计算到第二天0点0分的秒数
        next_run = (now.replace(hour=0, minute=0, second=0, microsecond=0) + 
                   asyncio.time_duration(days=1))
        wait_seconds = (next_run - now).total_seconds()
        
        await asyncio.sleep(wait_seconds)
        
        # 双重时间验证
        if datetime.now().hour != 0:
            continue
            
        today = datetime.now().strftime("%m-%d")
        logger.info(f"开始PJSK每日生日检查: {today}")
        
        try:
            bot = nonebot.get_bot()
            await send_birthday_notification(bot)
        except Exception as e:
            logger.error(f"PJSK生日定时任务执行失败: {e}")

@get_driver().on_startup
async def startup():
    """启动时加载配置"""
    load_config()
    # 启动定时任务
    asyncio.create_task(pjsk_birthday_scheduler())
    logger.info("PJSK生日推送插件已启动")
    logger.info("推送时间: 每天 00:00")

# 命令注册
from nonebot import on_command
from nonebot.params import CommandArg

birthday_list_cmd = on_command("pjsk生日列表", aliases={"pjsk生日", "pjsksr"}, priority=5, block=True)
test_character_cmd = on_command("pjsk测试角色", aliases={"测试pjsk角色", "pjsktest"}, priority=5, block=True)

@birthday_list_cmd.handle()
async def handle_birthday_list(bot: Bot, arg: Message = CommandArg()):
    """查看PJSK角色生日列表"""
    character_list = "🎂 PJSK角色生日列表:\n\n"
    for group_id, group_data in characters_config.items():
        if group_id == "plugin_config":
            continue
        
        group_comment = group_data.get("comment", group_id)
        character_list += f"【{group_comment}】\n"
        
        for char_id, char_config in group_data.items():
            if char_id == "comment":
                continue
            if isinstance(char_config, dict):
                character_list += f"{char_config.get('name', '未知')}: {char_config.get('birthday', '未知')}\n"
        
        character_list += "\n"
    
    await birthday_list_cmd.finish(character_list.strip())

@test_character_cmd.handle()
async def handle_test_character(bot: Bot, arg: Message = CommandArg()):
    """测试指定角色生日推送"""
    character_name = arg.extract_plain_text().strip()
    if not character_name:
        await test_character_cmd.finish("请指定要测试的角色名，例如: /pjsk测试角色 初音未来")
    
    try:
        await test_character_cmd.send(f"正在测试角色: {character_name}...")
        
        # 执行测试
        success, result_msg = await send_test_character(bot, character_name)
        
        # 发送最终结果并结束命令
        if success:
            await test_character_cmd.finish(f"✅ {result_msg}")
        else:
            await test_character_cmd.finish(f"❌ {result_msg}")
            
    except Exception as e:
        from nonebot.exception import FinishedException
        if isinstance(e, FinishedException):
            return 
        
        # 其他异常才记录和发送错误
        logger.error(f"测试角色 {character_name} 时发生错误: {e}")
        await test_character_cmd.finish(f"❌ 测试过程发生错误: {e}")