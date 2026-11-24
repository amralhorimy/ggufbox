from app.core.resources import MB, estimate_memory


def test_larger_context_costs_more():
    small = estimate_memory(4_000_000_000, 2048)
    large = estimate_memory(4_000_000_000, 16384)
    assert large.total_bytes > small.total_bytes


def test_gpu_offload_lowers_ram_estimate():
    cpu = estimate_memory(4_000_000_000, 4096, n_gpu_layers=0)
    gpu = estimate_memory(4_000_000_000, 4096, n_gpu_layers=-1)
    assert gpu.total_bytes < cpu.total_bytes
    assert gpu.overhead_bytes == 400 * MB
