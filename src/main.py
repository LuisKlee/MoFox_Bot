# 再用这个就写一行注释来混提交的我直接全部🌿飞😡
# 主系统入口文件 - 负责初始化和管理聊天机器人的所有核心组件
import asyncio
import signal
import sys
import time

from maim_message import MessageServer
from rich.traceback import install

from src.chat.emoji_system.emoji_manager import get_emoji_manager
from src.chat.memory_system.Hippocampus import hippocampus_manager
from src.chat.message_receive.bot import chat_bot
from src.chat.message_receive.chat_stream import get_chat_manager
from src.chat.utils.statistic import OnlineTimeRecordTask, StatisticOutputTask
from src.common.logger import get_logger
# 消息API和全局服务器管理
from src.common.message import get_global_api
from src.common.remote import TelemetryHeartBeatTask
from src.common.server import get_global_server, Server
from src.config.config import global_config
from src.individuality.individuality import get_individuality, Individuality
from src.manager.async_task_manager import async_task_manager
from src.mood.mood_manager import mood_manager
from src.plugin_system.base.component_types import EventType
from src.plugin_system.core.event_manager import event_manager
from src.plugin_system.core.plugin_hot_reload import hot_reload_manager
# 插件系统管理
from src.plugin_system.core.plugin_manager import plugin_manager
from src.schedule.monthly_plan_manager import monthly_plan_manager
from src.schedule.schedule_manager import schedule_manager

# 如果禁用了记忆功能，使用模拟的记忆管理器
if not global_config.memory.enable_memory:
    import src.chat.memory_system.Hippocampus as hippocampus_module

    class MockHippocampusManager:
        """模拟的记忆管理器，当记忆功能被禁用时使用"""
        def initialize(self):
            pass

        async def initialize_async(self):
            pass

        @staticmethod
        def get_hippocampus():
            return None

        async def build_memory(self):
            pass

        async def forget_memory(self, percentage: float = 0.005):
            pass

        async def consolidate_memory(self):
            pass

        @staticmethod
        async def get_memory_from_text(
                text: str,
                max_memory_num: int = 3,
                max_memory_length: int = 2,
                max_depth: int = 3,
                fast_retrieval: bool = False,
            ) -> list[str]:
            return []

        @staticmethod
        async def get_memory_from_topic(
                valid_keywords: list[str], max_memory_num: int = 3, max_memory_length: int = 2, max_depth: int = 3
        ) -> list[str]:
            return []

        @staticmethod
        async def get_activate_from_text(
                text: str, max_depth: int = 3, fast_retrieval: bool = False
        ) -> tuple[float, list[str]]:
            return 0.0, []

        @staticmethod
        def get_memory_from_keyword(keyword: str, max_depth: int = 2) -> list[str]:
            return []

        @staticmethod
        def get_all_node_names() -> list[str]:
            return []

    hippocampus_module.hippocampus_manager = MockHippocampusManager()

# 插件系统现在使用统一的插件加载器
install(extra_lines=3)

logger = get_logger("main")


class MainSystem:
    def __init__(self):
        self.hippocampus_manager = hippocampus_manager

        self.individuality: Individuality = get_individuality()

        # 使用消息API替代直接的FastAPI实例
        self.app: MessageServer = get_global_api()
        self.server: Server = get_global_server()

        # 设置信号处理器用于优雅退出
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """设置信号处理器"""

        def signal_handler(signum, frame):
            logger.info("收到退出信号，正在优雅关闭系统...")
            self._cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _cleanup(self):
        """清理资源"""
        try:
            # 触发停止事件
            import asyncio
            asyncio.run(event_manager.trigger_event(EventType.ON_STOP, permission_group="SYSTEM"))
        except Exception as e:
            logger.error(f"触发停止事件时出错: {e}")

        try:
            # 停止消息重组器
            from src.utils.message_chunker import reassembler
            
            # 检查事件循环状态
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(reassembler.stop_cleanup_task())
                else:
                    loop.run_until_complete(reassembler.stop_cleanup_task())
                logger.info("🛑 消息重组器已停止")
            except RuntimeError as e:
                logger.warning(f"事件循环不可用: {e}")
        except Exception as e:
            logger.error(f"停止消息重组器时出错: {e}")

        try:
            # 停止插件热重载系统
            hot_reload_manager.stop()
            logger.info("🛑 插件热重载系统已停止")
        except Exception as e:
            logger.error(f"停止热重载系统时出错: {e}")

        try:
            # 停止异步记忆管理器
            if global_config.memory.enable_memory:
                from src.chat.memory_system.async_memory_optimizer import async_memory_manager
                import asyncio

                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(async_memory_manager.shutdown())
                    else:
                        loop.run_until_complete(async_memory_manager.shutdown())
                    logger.info("🛑 记忆管理器已停止")
                except RuntimeError as e:
                    logger.warning(f"事件循环不可用: {e}")
        except Exception as e:
            logger.error(f"停止记忆管理器时出错: {e}")

    async def initialize(self):
        """初始化系统组件"""
        # 检查必要的配置
        if not hasattr(global_config, 'bot') or not hasattr(global_config.bot, 'nickname'):
            logger.error("缺少必要的bot配置")
            raise ValueError("Bot配置不完整")
            
        logger.info(f"正在唤醒{global_config.bot.nickname}......")

        # 其他初始化任务
        await asyncio.gather(self._init_components())
        phrases = [
            ("我们的代码里真的没有bug，只有‘特性'.", 10),
            ("你知道吗？阿范喜欢被切成臊子😡", 10),  # 修复了语法错误
            ("你知道吗,雅诺狐的耳朵其实很好摸", 5),
            ("你群最高技术力————言柒姐姐！", 20),
            ("初墨小姐宇宙第一(不是)", 10),
            ("world.execute(me);", 10),
            ("正在尝试连接到MaiBot的服务器...连接失败...，正在转接到maimaiDX", 10),
            ("你的bug就像星星一样多，而我的代码像太阳一样，一出来就看不见了。", 10),
            ("温馨提示：请不要在代码中留下任何魔法数字，除非你知道它的含义。", 10),
            ("世界上只有10种人：懂二进制的和不懂的。", 10),
            ("喵喵~你的麦麦被猫娘入侵了喵~", 15),
            ("恭喜你触发了稀有彩蛋喵：诺狐嗷呜~ ~", 1),
            ("恭喜你！！！你的开发者模式已成功开启，快来加入我们吧！(๑•̀ㅂ•́)و✧   (小声bb:其实是当黑奴)", 10),
        ]
        from random import choices

        # 分离彩蛋和权重
        egg_texts, weights = zip(*phrases)

        # 使用choices进行带权重的随机选择
        selected_egg = choices(egg_texts, weights=weights, k=1)
        eggs = selected_egg[0]
        logger.info(f"""
全部系统初始化完成，{global_config.bot.nickname}已成功唤醒
=========================================================
MoFox_Bot(第三方修改版)
全部组件已成功启动!
=========================================================
🌐 项目地址: https://github.com/MoFox-Studio/MoFox_Bot
🏠 官方项目: https://github.com/MaiM-with-u/MaiBot
=========================================================
这是基于原版MMC的社区改版，包含增强功能和优化(同时也有更多的'特性')
=========================================================
小贴士:{eggs}
""")

    async def _init_components(self):
        """初始化其他组件"""
        init_start_time = time.time()

        # 添加在线时间统计任务
        await async_task_manager.add_task(OnlineTimeRecordTask())

        # 添加统计信息输出任务
        await async_task_manager.add_task(StatisticOutputTask())
        
        # 添加遥测心跳任务
        await async_task_manager.add_task(TelemetryHeartBeatTask())

        # 注册默认事件
        event_manager.init_default_events()

        # 初始化权限管理器
        from src.plugin_system.core.permission_manager import PermissionManager
        from src.plugin_system.apis.permission_api import permission_api

        permission_manager = PermissionManager()
        await permission_manager.initialize()
        permission_api.set_permission_manager(permission_manager)
        logger.info("权限管理器初始化成功")

        # 加载所有actions，包括默认的和插件的
        plugin_manager.load_all_plugins()

        # 处理所有缓存的事件订阅（插件加载完成后）
        event_manager.process_all_pending_subscriptions()

        # 启动插件热重载系统
        hot_reload_manager.start()

        # 初始化表情管理器
        get_emoji_manager().initialize()
        logger.info("表情包管理器初始化成功")

        # 启动情绪管理器
        await mood_manager.start()
        logger.info("情绪管理器初始化成功")

        # 初始化聊天管理器
        await get_chat_manager()._initialize()
        asyncio.create_task(get_chat_manager()._auto_save_task())
        logger.info("聊天管理器初始化成功")

        # 初始化记忆系统
        if global_config.memory.enable_memory:
            await self.hippocampus_manager.initialize_async()
            logger.info("记忆系统初始化成功")
        else:
            logger.info("记忆系统已禁用，跳过初始化")

        # 初始化LPMM知识库
        from src.chat.knowledge.knowledge_lib import initialize_lpmm_knowledge
        initialize_lpmm_knowledge()
        logger.info("LPMM知识库初始化成功")

        # 初始化异步记忆管理器
        try:
            if global_config.memory.enable_memory:
                from src.chat.memory_system.async_memory_optimizer import async_memory_manager
                await async_memory_manager.initialize()
                logger.info("记忆管理器初始化成功")
            else:
                logger.info("记忆管理器已禁用，跳过初始化")
        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")

        # 将bot.py中的chat_bot.message_process消息处理函数注册到api.py的消息处理基类中
        self.app.register_message_handler(chat_bot.message_process)

        # 启动消息重组器的清理任务
        from src.utils.message_chunker import reassembler
        await reassembler.start_cleanup_task()
        logger.info("消息重组器已启动")

        # 初始化个体特征
        await self.individuality.initialize()

        # 初始化月度计划管理器
        if global_config.planning_system.monthly_plan_enable:
            logger.info("正在初始化月度计划管理器...")
            try:
                await monthly_plan_manager.initialize()
                logger.info("月度计划管理器初始化成功")
            except Exception as e:
                logger.error(f"月度计划管理器初始化失败: {e}")

        # 初始化日程管理器
        if global_config.planning_system.schedule_enable:
            logger.info("日程表功能已启用，正在初始化管理器...")
            await schedule_manager.initialize()
            logger.info("日程表管理器初始化成功。")

        try:
            await event_manager.trigger_event(EventType.ON_START, permission_group="SYSTEM")
            init_time = int(1000 * (time.time() - init_start_time))
            logger.info(f"初始化完成，神经元放电{init_time}次")
        except Exception as e:
            logger.error(f"启动大脑和外部世界失败: {e}")
            raise

    async def schedule_tasks(self):
        """调度定时任务"""
        while True:
            tasks = [
                get_emoji_manager().start_periodic_check_register(),
                self.app.run(),
                self.server.run(),
            ]

            # 添加记忆系统相关任务（仅在启用时）
            if global_config.memory.enable_memory:
                tasks.extend(
                    [
                        self.build_memory_task(),
                        self.forget_memory_task(),
                        self.consolidate_memory_task(),
                    ]
                )

            await asyncio.gather(*tasks)

    async def build_memory_task(self):
        """记忆构建任务"""
        while True:
            await asyncio.sleep(global_config.memory.memory_build_interval)
            
            try:
                # 检查记忆功能是否启用
                if not global_config.memory.enable_memory:
                    continue
                    
                # 使用异步记忆管理器进行非阻塞记忆构建
                from src.chat.memory_system.async_memory_optimizer import build_memory_nonblocking

                logger.info("正在启动记忆构建")
                
                # 启动异步构建
                task_id = await build_memory_nonblocking()
                if task_id:
                    logger.info(f"记忆构建任务已提交：{task_id}")
                else:
                    logger.warning("记忆构建任务提交失败")
                    
            except ImportError:
                logger.warning("记忆优化器不可用，跳过记忆构建")
            except Exception as e:
                logger.error(f"记忆构建任务启动失败: {e}")

    async def forget_memory_task(self):
        """记忆遗忘任务"""
        while True:
            await asyncio.sleep(global_config.memory.forget_memory_interval)
            # 检查记忆功能是否启用
            if not global_config.memory.enable_memory:
                continue
                
            logger.info("[记忆遗忘] 开始遗忘记忆...")
            await self.hippocampus_manager.forget_memory(percentage=global_config.memory.memory_forget_percentage)
            logger.info("[记忆遗忘] 记忆遗忘完成")

    async def consolidate_memory_task(self):
        """记忆整合任务"""
        while True:
            await asyncio.sleep(global_config.memory.consolidate_memory_interval)
            # 检查记忆功能是否启用
            if not global_config.memory.enable_memory:
                continue
                
            logger.info("[记忆整合] 开始整合记忆...")
            await self.hippocampus_manager.consolidate_memory()
            logger.info("[记忆整合] 记忆整合完成")


async def main():
    """主函数"""
    system = MainSystem()
    await asyncio.gather(
        system.initialize(),
        system.schedule_tasks(),
    )


if __name__ == "__main__":
    asyncio.run(main())
