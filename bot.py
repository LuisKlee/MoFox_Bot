# import asyncio
import asyncio
import os
import sys
import time
import platform
import traceback
from pathlib import Path
from rich.traceback import install
from colorama import init, Fore
from dotenv import load_dotenv  # 处理.env文件

# maim_message imports for console input

# 最早期初始化日志系统，确保所有后续模块都使用正确的日志格式
from src.common.logger import initialize_logging, get_logger, shutdown_logging

# UI日志适配器
initialize_logging()

from src.main import MainSystem  # noqa
from src import BaseMain  # noqa
from src.manager.async_task_manager import async_task_manager  # noqa
from src.chat.knowledge.knowledge_lib import initialize_lpmm_knowledge # noqa
from src.config.config import global_config  # noqa
from src.common.database.database import initialize_sql_database  # noqa
from src.common.database.sqlalchemy_models import initialize_database as init_db  # noqa

logger = get_logger("main")

install(extra_lines=3)

# 设置工作目录为脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
logger.info(f"已设置工作目录为: {script_dir}")

# 检查并创建.env文件
def ensure_env_file():
    """确保.env文件存在，如果不存在则从模板创建"""
    # 定义.env文件的路径
    env_file = Path(".env")
    # 定义模板文件的路径
    template_env = Path("template/template.env")
    
    # 检查.env文件是否存在
    if not env_file.exists():
        # 检查模板文件是否存在
        if template_env.exists():
            # 记录日志：未找到.env文件，正在从模板创建
            logger.info("未找到.env文件，正在从模板创建...")
            # 导入shutil模块用于文件复制
            import shutil
            # 复制模板文件到.env文件
            shutil.copy(template_env, env_file)
            # 记录日志：已从template/template.env创建.env文件
            logger.info("已从template/template.env创建.env文件")
            # 记录日志：提示用户编辑.env文件
            logger.warning("请编辑.env文件，将EULA_CONFIRMED设置为true并配置其他必要参数")
        else:
            # 记录日志：未找到.env文件和template.env模板文件
            logger.error("未找到.env文件和template.env模板文件")
            # 退出程序
            sys.exit(1)

# 确保环境文件存在
ensure_env_file()

# 加载环境变量
load_dotenv()

confirm_logger = get_logger("confirm")
# 获取没有加载env时的环境变量

uvicorn_server = None
driver = None
app = None
loop = None


async def request_shutdown() -> bool:
    """请求关闭程序"""
    try:
        if loop and not loop.is_closed():  # 检查事件循环是否存在且未关闭
            try:
                loop.run_until_complete(graceful_shutdown())  # 在事件循环中执行优雅关闭
            except Exception as ge:  # 捕捉优雅关闭时可能发生的错误
                logger.error(f"优雅关闭时发生错误: {ge}")  # 记录错误信息
                return False  # 返回False表示关闭失败
        return True  # 返回True表示关闭成功
    except Exception as e:  # 捕获执行过程中可能发生的其他错误
        logger.error(f"请求关闭程序时发生错误: {e}")  # 记录错误信息
        return False  # 返回False表示关闭失败


def easter_egg():
    # 彩蛋
    init()
    text = "多年以后，面对AI行刑队，张三将会回想起他2023年在会议上讨论人工智能的那个下午"
    rainbow_colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    rainbow_text = ""
    for i, char in enumerate(text):
        rainbow_text += rainbow_colors[i % len(rainbow_colors)] + char
    logger.info(rainbow_text)


async def graceful_shutdown():
    """优雅关闭程序 - 增强版本"""
    try:
        logger.info("正在优雅关闭麦麦...")
        
        # 记录开始关闭时间
        start_time = time.time()
        
        # 停止所有异步任务
        await async_task_manager.stop_and_wait_all_tasks()

        # 获取所有剩余任务，排除当前任务
        remaining_tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

        if remaining_tasks:
            logger.info(f"正在取消 {len(remaining_tasks)} 个剩余任务...")

            # 取消所有剩余任务
            for task in remaining_tasks:
                if not task.done():
                    task.cancel()

            # 等待所有任务完成，设置超时
            try:
                await asyncio.wait_for(asyncio.gather(*remaining_tasks, return_exceptions=True), timeout=15.0)
                logger.info("所有剩余任务已成功取消")
            except asyncio.TimeoutError:
                logger.warning("等待任务取消超时，强制继续关闭")
            except Exception as e:
                logger.error(f"等待任务取消时发生异常: {e}")

        # 记录关闭耗时
        shutdown_time = time.time() - start_time
        logger.info(f"麦麦优雅关闭完成，耗时: {shutdown_time:.2f}秒")

    except Exception as e:
        logger.error(f"麦麦关闭失败: {e}", exc_info=True)
    finally:
        # 确保日志系统关闭
        try:
            shutdown_logging()
        except Exception as e:
            print(f"关闭日志系统时出错: {e}")


def check_eula():
    """检查EULA和隐私条款确认状态 - 环境变量版（类似Minecraft）"""
    # 检查环境变量中的EULA确认
    eula_confirmed = os.getenv('EULA_CONFIRMED', '').lower()
    
    if eula_confirmed == 'true':
        logger.info("EULA已通过环境变量确认")
        return
    
    # 如果没有确认，提示用户
    confirm_logger.critical("您需要同意EULA和隐私条款才能使用MoFox_Bot")
    confirm_logger.critical("请阅读以下文件：")
    confirm_logger.critical("  - EULA.md (用户许可协议)")
    confirm_logger.critical("  - PRIVACY.md (隐私条款)")
    confirm_logger.critical("然后编辑 .env 文件，将 'EULA_CONFIRMED=false' 改为 'EULA_CONFIRMED=true'")
    
    # 等待用户确认
    while True:
        try:
            load_dotenv(override=True)  # 重新加载.env文件
                
            eula_confirmed = os.getenv('EULA_CONFIRMED', '').lower()
            if eula_confirmed == 'true':
                confirm_logger.info("EULA确认成功，感谢您的同意")
                return
                
            confirm_logger.critical("请修改 .env 文件中的 EULA_CONFIRMED=true 后重新启动程序")
            input("按Enter键检查.env文件状态...")
            
        except KeyboardInterrupt:
            confirm_logger.info("用户取消，程序退出")
            sys.exit(0)
        except Exception as e:
            confirm_logger.error(f"检查EULA状态失败: {e}")
            sys.exit(1)


def validate_configuration():
    """验证关键配置"""
    try:
        # 基础配置验证
        if not hasattr(global_config, 'database'):
            logger.error("配置中缺少database配置")
            return False
            
        # 验证数据库配置
        db_config = global_config.database
        required_fields = ['database_type', 'host']
        
        for field in required_fields:
            if not getattr(db_config, field, None):
                logger.error(f"数据库配置缺少必要字段: {field}")
                return False
        
        # 验证数据库类型
        supported_dbs = ['sqlite', 'mysql', 'postgresql']
        if db_config.database_type not in supported_dbs:
            logger.error(f"不支持的数据库类型: {db_config.database_type}")
            return False
            
        logger.info("配置验证通过")
        return True
        
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        return False


class MaiBotMain(BaseMain):
    """麦麦机器人主程序类"""

    def __init__(self):
        """
        初始化方法，用于创建类的实例时执行
        继承父类的初始化方法，并初始化实例属性
        """
        super().__init__()  # 调用父类的初始化方法
        self.main_system = None  # 初始化主系统属性为None

    def setup_timezone(self):
        """设置时区"""
        try:
            if platform.system().lower() != "windows":
                time.tzset()  # type: ignore
                logger.info("时区设置完成")
            else:
                logger.info("Windows系统，跳过时区设置")
        except Exception as e:
            logger.warning(f"时区设置失败: {e}")

    def check_and_confirm_eula(self):
        """检查并确认EULA和隐私条款"""
        logger.info("开始检查EULA和隐私条款...")
        check_eula()
        logger.info("检查EULA和隐私条款完成")

    def initialize_database(self):
        """初始化数据库连接"""
        logger.info("正在初始化数据库连接...")
        try:
            start_time = time.time()
            initialize_sql_database(global_config.database)
            elapsed_time = time.time() - start_time
            logger.info(f"数据库连接初始化成功，使用 {global_config.database.database_type} 数据库，耗时: {elapsed_time:.2f}秒")
        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise e

    async def initialize_database_async(self):
        """异步初始化数据库表结构"""
        logger.info("正在初始化数据库表结构...")
        try:
            start_time = time.time()
            await init_db()
            elapsed_time = time.time() - start_time
            logger.info(f"数据库表结构初始化完成，耗时: {elapsed_time:.2f}秒")
        except Exception as e:
            logger.error(f"数据库表结构初始化失败: {e}")
            raise e

    def create_main_system(self):
        """创建MainSystem实例"""  # 这是一个多行注释，用于描述函数的功能
        self.main_system = MainSystem()  # 创建MainSystem类的实例并赋值给self.main_system
        return self.main_system  # 返回创建的MainSystem实例

    def run(self):
        """运行主程序"""
        # 执行初始化流程
        self.setup_timezone()
        self.check_and_confirm_eula()
        
        # 验证配置
        if not validate_configuration():
            raise RuntimeError("配置验证失败，请检查配置文件")
            
        self.initialize_database()
        return self.create_main_system()


if __name__ == "__main__":
    exit_code = 0  # 用于记录程序最终的退出状态
    try:
        # 创建MaiBotMain实例并获取MainSystem
        maibot = MaiBotMain()
        main_system = maibot.run()

        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 异步初始化数据库表结构
            loop.run_until_complete(maibot.initialize_database_async())
            
            # 执行初始化和任务调度
            loop.run_until_complete(main_system.initialize())
            initialize_lpmm_knowledge()
            
            # 显示彩蛋
            easter_egg()
            
            # Schedule tasks returns a future that runs forever.
            # We can run console_input_loop concurrently.
            main_tasks = loop.create_task(main_system.schedule_tasks())
            logger.info("麦麦机器人启动完成，开始运行主任务...")
            loop.run_until_complete(main_tasks)

        except KeyboardInterrupt:
            logger.warning("收到中断信号，正在优雅关闭...")
        except Exception as e:
            logger.error(f"主任务执行异常: {e}")
            raise

    except KeyboardInterrupt:
        logger.info("程序启动过程中被用户中断")
        exit_code = 130
    except Exception as e:
        logger.error(f"主程序发生异常: {str(e)}")
        logger.debug(f"异常详情: {traceback.format_exc()}")
        exit_code = 1  # 标记发生错误
    finally:
        # 确保 loop 在任何情况下都尝试关闭（如果存在且未关闭）
        if "loop" in locals() and loop and not loop.is_closed():
            logger.info("开始执行最终关闭流程...")
            try:
                loop.run_until_complete(graceful_shutdown())
            except Exception as ge:
                logger.error(f"优雅关闭时发生错误: {ge}")
            finally:
                loop.close()
                logger.info("事件循环已关闭")
        else:
            # 如果没有事件循环，仍然尝试关闭日志系统
            try:
                shutdown_logging()
            except Exception as e:
                print(f"关闭日志系统时出错: {e}")

        # 在程序退出前暂停，让你有机会看到输出
        if exit_code != 0 or os.getenv('ENVIRONMENT') != 'production':
            try:
                input("按 Enter 键退出...")
            except (KeyboardInterrupt, EOFError):
                pass  # 忽略中断错误

        sys.exit(exit_code)  # <--- 使用记录的退出码
