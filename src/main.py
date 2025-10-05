# 再用这个就写一行注释来混提交的我直接全部🌿飞😡
# 主系统入口文件 - 负责初始化和管理聊天机器人的所有核心组件
import asyncio
import signal
import sys

@@ -13,7 +14,7 @@ from src.chat.message_receive.bot import chat_bot
from src.chat.message_receive.chat_stream import get_chat_manager
from src.chat.utils.statistic import OnlineTimeRecordTask, StatisticOutputTask
from src.common.logger import get_logger
# 导入消息API和traceback模块
# 消息API和全局服务器管理
from src.common.message import get_global_api
from src.common.remote import TelemetryHeartBeatTask
from src.common.server import get_global_server, Server

@@ -24,17 +25,17 @@ from src.mood.mood_manager import mood_manager
from src.plugin_system.base.component_types import EventType
from src.plugin_system.core.event_manager import event_manager
from src.plugin_system.core.plugin_hot_reload import hot_reload_manager
# 导入新的插件管理器和热重载管理器
# 插件系统管理
from src.plugin_system.core.plugin_manager import plugin_manager
from src.schedule.monthly_plan_manager import monthly_plan_manager
from src.schedule.schedule_manager import schedule_manager

# from src.api.main import start_api_server

# 如果禁用了记忆功能，使用模拟的记忆管理器
if not global_config.memory.enable_memory:
    import src.chat.memory_system.Hippocampus as hippocampus_module

    class MockHippocampusManager:
        """模拟的记忆管理器，当记忆功能被禁用时使用"""
        def initialize(self):
            pass


@@ -57,17 +58,17 @@ if not global_config.memory.enable_memory:
        @staticmethod
        async def get_memory_from_text(
                text: str,
            max_memory_num: int = 3,
            max_memory_length: int = 2,
            max_depth: int = 3,
            fast_retrieval: bool = False,
        ) -> list:
                max_memory_num: int = 3,
                max_memory_length: int = 2,
                max_depth: int = 3,
                fast_retrieval: bool = False,
            ) -> list[str]:
            return []

        @staticmethod
        async def get_memory_from_topic(
                valid_keywords: list[str], max_memory_num: int = 3, max_memory_length: int = 2, max_depth: int = 3
        ) -> list:
        ) -> list[str]:
            return []

        @staticmethod

@@ -77,17 +78,16 @@ if not global_config.memory.enable_memory:
            return 0.0, []

        @staticmethod
        def get_memory_from_keyword(keyword: str, max_depth: int = 2) -> list:
        def get_memory_from_keyword(keyword: str, max_depth: int = 2) -> list[str]:
            return []

        @staticmethod
        def get_all_node_names() -> list:
        def get_all_node_names() -> list[str]:
            return []

    hippocampus_module.hippocampus_manager = MockHippocampusManager()

# 插件系统现在使用统一的插件加载器

install(extra_lines=3)

logger = get_logger("main")


@@ -117,23 +117,29 @@ class MainSystem:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @staticmethod
    def _cleanup():
    def _cleanup(self):
        """清理资源"""
        try:
            # 停止消息重组器
            from src.plugin_system.core.event_manager import event_manager
            from src.plugin_system import EventType
            # 触发停止事件
            import asyncio
            asyncio.run(event_manager.trigger_event(EventType.ON_STOP,permission_group="SYSTEM"))
            from src.utils.message_chunker import reassembler
            asyncio.run(event_manager.trigger_event(EventType.ON_STOP, permission_group="SYSTEM"))
        except Exception as e:
            logger.error(f"触发停止事件时出错: {e}")

            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(reassembler.stop_cleanup_task())
            else:
                loop.run_until_complete(reassembler.stop_cleanup_task())
            logger.info("🛑 消息重组器已停止")
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


@@ -150,27 +156,35 @@ class MainSystem:
                from src.chat.memory_system.async_memory_optimizer import async_memory_manager
                import asyncio

                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(async_memory_manager.shutdown())
                else:
                    loop.run_until_complete(async_memory_manager.shutdown())
                logger.info("🛑 记忆管理器已停止")
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
            ("我们的代码里真的没有bug，只有‘特性’.", 10),
            ("你知道吗？阿范喜欢被切成臊子😡", 10),  # 你加的提示出语法问题来了😡😡😡😡😡😡😡
            ("我们的代码里真的没有bug，只有‘特性'.", 10),
            ("你知道吗？阿范喜欢被切成臊子😡", 10),  # 修复了语法错误
            ("你知道吗,雅诺狐的耳朵其实很好摸", 5),
            ("你群最高技术力————言柒姐姐！", 20),
            ("初墨小姐宇宙第一(不是)", 10),  # 15
            ("初墨小姐宇宙第一(不是)", 10),
            ("world.execute(me);", 10),
            ("正在尝试连接到MaiBot的服务器...连接失败...，正在转接到maimaiDX", 10),
            ("你的bug就像星星一样多，而我的代码像太阳一样，一出来就看不见了。", 10),

@@ -183,7 +197,7 @@ class MainSystem:
        from random import choices

        # 分离彩蛋和权重
        egg_texts, weights = zip(*phrases, strict=True)
        egg_texts, weights = zip(*phrases)

        # 使用choices进行带权重的随机选择
        selected_egg = choices(egg_texts, weights=weights, k=1)


@@ -227,10 +241,6 @@ MoFox_Bot(第三方修改版)
        permission_api.set_permission_manager(permission_manager)
        logger.info("权限管理器初始化成功")

        # 启动API服务器
        # start_api_server()
        # logger.info("API服务器启动成功")

        # 加载所有actions，包括默认的和插件的
        plugin_manager.load_all_plugins()


@@ -249,15 +259,16 @@ MoFox_Bot(第三方修改版)
        logger.info("情绪管理器初始化成功")

        # 初始化聊天管理器

        await get_chat_manager()._initialize()
        asyncio.create_task(get_chat_manager()._auto_save_task())

        logger.info("聊天管理器初始化成功")

        # 初始化记忆系统
        await self.hippocampus_manager.initialize_async()
        logger.info("记忆系统初始化成功")
        if global_config.memory.enable_memory:
            await self.hippocampus_manager.initialize_async()
            logger.info("记忆系统初始化成功")
        else:
            logger.info("记忆系统已禁用，跳过初始化")

        # 初始化LPMM知识库
        from src.chat.knowledge.knowledge_lib import initialize_lpmm_knowledge

@@ -266,21 +277,20 @@ MoFox_Bot(第三方修改版)

        # 初始化异步记忆管理器
        try:
            from src.chat.memory_system.async_memory_optimizer import async_memory_manager

            await async_memory_manager.initialize()
            logger.info("记忆管理器初始化成功")
            if global_config.memory.enable_memory:
                from src.chat.memory_system.async_memory_optimizer import async_memory_manager
                await async_memory_manager.initialize()
                logger.info("记忆管理器初始化成功")
            else:
                logger.info("记忆管理器已禁用，跳过初始化")
        except Exception as e:
            logger.error(f"记忆管理器初始化失败: {e}")

        # await asyncio.sleep(0.5) #防止logger输出飞了

        # 将bot.py中的chat_bot.message_process消息处理函数注册到api.py的消息处理基类中
        self.app.register_message_handler(chat_bot.message_process)

        # 启动消息重组器的清理任务
        from src.utils.message_chunker import reassembler

        await reassembler.start_cleanup_task()
        logger.info("消息重组器已启动")



@@ -319,14 +329,15 @@ MoFox_Bot(第三方修改版)
                self.server.run(),
            ]

            # 添加记忆系统相关任务
            tasks.extend(
                [
                    self.build_memory_task(),
                    self.forget_memory_task(),
                    self.consolidate_memory_task(),
                ]
            )
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


@@ -334,65 +345,51 @@ MoFox_Bot(第三方修改版)
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

                # 定义构建完成的回调函数
                def build_completed(result):
                    if result:
                        logger.info("记忆构建完成")
                    else:
                        logger.warning("记忆构建失败")

                # 启动异步构建，不等待完成
                
                # 启动异步构建
                task_id = await build_memory_nonblocking()
                logger.info(f"记忆构建任务已提交：{task_id}")

                if task_id:
                    logger.info(f"记忆构建任务已提交：{task_id}")
                else:
                    logger.warning("记忆构建任务提交失败")
                    
            except ImportError:
                # 如果异步优化器不可用，使用原有的同步方式（但在单独的线程中运行）
                logger.warning("记忆优化器不可用，使用线性运行执行记忆构建")

                def sync_build_memory():
                    """在线程池中执行同步记忆构建"""
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        result = loop.run_until_complete(self.hippocampus_manager.build_memory())
                        logger.info("记忆构建完成")
                        return result
                    except Exception as e:
                        logger.error(f"记忆构建失败: {e}")
                        return None
                    finally:
                        loop.close()

                # 在线程池中执行记忆构建
                asyncio.get_event_loop().run_in_executor(None, sync_build_memory)

                logger.warning("记忆优化器不可用，跳过记忆构建")
            except Exception as e:
                logger.error(f"记忆构建任务启动失败: {e}")
                # fallback到原有的同步方式
                logger.info("正在进行记忆构建（同步模式）")
                await self.hippocampus_manager.build_memory()  # type: ignore

    async def forget_memory_task(self):
        """记忆遗忘任务"""
        while True:
            await asyncio.sleep(global_config.memory.forget_memory_interval)
            # 检查记忆功能是否启用
            if not global_config.memory.enable_memory:
                continue
                
            logger.info("[记忆遗忘] 开始遗忘记忆...")
            await self.hippocampus_manager.forget_memory(percentage=global_config.memory.memory_forget_percentage)  # type: ignore
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
            await self.hippocampus_manager.consolidate_memory()  # type: ignore
            await self.hippocampus_manager.consolidate_memory()
            logger.info("[记忆整合] 记忆整合完成")
