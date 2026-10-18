"""Host-localhost TCP to shared Unix socket; no third-party dependencies."""
import argparse
import asyncio
from pathlib import Path


async def serve(socket_path, port):
    async def connection(reader, writer):
        upstream = None
        async def copy(source, destination):
            while data := await asyncio.wait_for(source.read(65536), 60):
                destination.write(data)
                await destination.drain()
        try:
            remote, upstream = await asyncio.open_unix_connection(str(socket_path))
            tasks = [asyncio.create_task(copy(reader, upstream)),
                     asyncio.create_task(copy(remote, writer))]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        except (OSError, TimeoutError):
            pass
        finally:
            writer.close()
            if upstream:
                upstream.close()

    server = await asyncio.start_server(connection, '127.0.0.1', port)
    print(f'GreenPulse private proxy: 127.0.0.1:{port}', flush=True)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--socket', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8003)
    args = parser.parse_args()
    asyncio.run(serve(args.socket, args.port))
