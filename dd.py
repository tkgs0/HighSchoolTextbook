#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""
环境要求: Python3.8 以上
安装依赖: pip install -U httpx rich
"""

from pathlib import Path
import asyncio, httpx
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TransferSpeedColumn,
)


# 文件目录
dirPath: str = "./人教版2019/数学_选修/D_音乐中的数学"

# 页数
pages: int = 118

# 文件列表
# 格式:
"""
  文件名   URL
  文件名1  URL
  文件名2  URL
"""
fileList: str = """

{i}.jpg   https://book.pep.com.cn/1421001238233/files/mobile/{i}.jpg

""".strip()

# 请求参数
params: dict = {}

# 请求头
headers: dict = {
    "User-Agent": "Mozilla/5.0 (Linux; arm64; Android 12; SM-S9080) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 YaBrowser/23.0.0.00.00 SA/3 Mobile Safari/537.36",
}

# 饼干
cookies: dict = {}

# 超时期限 (秒)
timeout: int = 120

# 并发数量
semaphore: int = 16


async def run() -> None:
    if not fileList:
        return
    down: list = []
    sem = asyncio.Semaphore(semaphore)
    for x in range(pages):
        filename, url = fileList.format(i=x+1).split()
        down.append(dload(sem=sem, url=url, filename=filename))
    with progress:
        await asyncio.gather(*down)
    progress.console.log("执行完毕.")


progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
)


async def dload(sem, url: str, filename: str) -> None:

    # 文件路径
    filePath: Path = (
        Path(dirPath.strip()) / filename.strip()
        if dirPath.strip()
        else Path(filename.strip())
    )
    filePath.parent.mkdir(parents=True, exist_ok=True)

    async with sem:  # 限制并发

        async with httpx.AsyncClient().stream(
            'GET', url=url.strip(),
            params=params, headers=headers, cookies=cookies,
            follow_redirects=True,
            timeout=timeout,
        ) as resp:
            if resp.status_code != 200:
                progress.console.log(f"{filename}: {resp.status_code}")
                return

            total = resp.headers.get("Content-Length")

            task_id = progress.add_task(  # 进度条
                "download",
                start=True,
                total=int(total) if total else None,
                filename=filename,
            )
            with open(filePath, 'wb') as fd:  # 写入文件
                async for chunk in resp.aiter_bytes(1024):
                    fd.write(chunk)
                    progress.update(
                        task_id,
                        advance=len(chunk),
                    )

            await asyncio.to_thread(progress.remove_task, task_id)


if __name__ == '__main__':
    asyncio.run(run())
