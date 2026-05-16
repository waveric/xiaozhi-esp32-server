#!/usr/bin/env python
"""
数据迁移脚本: 将 lightning-tools/data/lightning.db 迁移到 xiaozhi-server/data/

功能:
1. 复制 lightning-tools/data/lightning.db -> xiaozhi-server/data/lightning.db
2. 验证迁移后数据库记录数一致
3. 脚本幂等: 目标已存在时提示是否覆盖

用法:
    python scripts/migrate_lightning_db.py [--force]

选项:
    --force    强制覆盖，不提示确认
"""

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path


# 路径配置 (相对于项目根目录)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SOURCE_DIR = PROJECT_ROOT.parent / "lightning-tools" / "data"
TARGET_DIR = PROJECT_ROOT / "main" / "xiaozhi-server" / "data"

SOURCE_DB = SOURCE_DIR / "lightning.db"
TARGET_DB = TARGET_DIR / "lightning.db"


def get_table_counts(db_path: Path) -> dict[str, int]:
    """获取数据库中所有表的记录数"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]

    conn.close()
    return counts


def verify_migration(source_db: Path, target_db: Path) -> bool:
    """验证迁移后的数据库记录数一致"""
    source_counts = get_table_counts(source_db)
    target_counts = get_table_counts(target_db)

    print("\n验证数据库记录数:")
    print(f"{'表名':<25} {'源数据库':>10} {'目标数据库':>10} {'状态':>8}")
    print("-" * 55)

    all_match = True
    for table in source_counts:
        source_count = source_counts[table]
        target_count = target_counts.get(table, 0)
        match = source_count == target_count
        status = "OK" if match else "FAIL"
        print(f"{table:<25} {source_count:>10} {target_count:>10} {status:>8}")
        if not match:
            all_match = False

    return all_match


def migrate_database(force: bool = False) -> bool:
    """执行数据库迁移"""
    # 检查源数据库
    if not SOURCE_DB.exists():
        print(f"错误: 源数据库不存在: {SOURCE_DB}")
        return False

    # 确保目标目录存在
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # 检查目标数据库是否已存在
    if TARGET_DB.exists():
        if not force:
            response = input(f"目标数据库已存在: {TARGET_DB}\n是否覆盖? (y/N): ")
            if response.lower() != 'y':
                print("取消迁移")
                return False
        print(f"删除现有数据库: {TARGET_DB}")
        TARGET_DB.unlink()

    # 复制数据库
    print(f"\n迁移数据库:")
    print(f"  源: {SOURCE_DB}")
    print(f"  目标: {TARGET_DB}")

    shutil.copy2(SOURCE_DB, TARGET_DB)
    print("数据库复制完成")

    # 验证迁移
    if verify_migration(SOURCE_DB, TARGET_DB):
        print("\n迁移成功! 数据库记录数一致")
        return True
    else:
        print("\n警告: 数据库记录数不一致，请检查迁移结果")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="迁移 lightning-tools 数据库到 xiaozhi-server"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制覆盖，不提示确认"
    )
    args = parser.parse_args()

    print("=" * 55)
    print("Lightning-Tools 数据库迁移脚本")
    print("=" * 55)
    print(f"\n项目根目录: {PROJECT_ROOT}")
    print(f"源目录: {SOURCE_DIR}")
    print(f"目标目录: {TARGET_DIR}")

    success = migrate_database(force=args.force)

    if success:
        print("\n下一步:")
        print(f"  1. 检查迁移后的数据库: {TARGET_DB}")
        print(f"  2. 重启 xiaozhi-server 服务")
        print(f"  3. 更新 MCP 配置，指向新的数据库路径")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
