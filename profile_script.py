import asyncio
import cProfile
import pstats
import io

from source.manager import BankNode
from source.models import State

async def heavy_load_test():
    '''Профилирование'''
    alex = BankNode()
    await alex.startup()
    alex.state = State(name="Alex", address="node-Alex", balance=1000.0)
    
    
    for i in range(100):
        await alex.make_tx("node-Boris", 5.0)
        await alex.save()

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.runcall(asyncio.run, heavy_load_test())
    
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    print(stream.getvalue())
        