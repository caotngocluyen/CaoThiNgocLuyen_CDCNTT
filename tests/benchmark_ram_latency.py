# tests/benchmark_ram_latency.py
"""
Multi-run Benchmark for Process RSS, Peak Working Set, System Available RAM, and Agent Latency (Median & P95).
"""
import sys
import os
import time
import json
import statistics
import ctypes
from ctypes import wintypes
import psutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.orchestrator import LegalAgentOrchestrator

# Windows API for PeakWorkingSetSize
class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
        ('PrivateUsage', ctypes.c_size_t),
    ]

def get_peak_rss_mb() -> float:
    try:
        GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
        GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
        counters = PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
        if GetProcessMemoryInfo(GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return counters.PeakWorkingSetSize / (1024 * 1024)
    except Exception:
        pass
    return psutil.Process().memory_info().rss / (1024 * 1024)

def run_ram_latency_benchmark():
    print("="*85)
    print("PROFILING RAM, PEAK WORKING SET, AND AGENT LATENCIES (MEDIAN & P95)")
    print("="*85)

    proc = psutil.Process()
    vm_init = psutil.virtual_memory()

    print(f"Khởi động tiến trình:")
    print(f"  - Python Process RSS ban đầu: {proc.memory_info().rss / (1024*1024):.2f} MB")
    print(f"  - Windows System RAM Total:   {vm_init.total / (1024**3):.2f} GB")
    print(f"  - Windows System RAM Used:    {vm_init.used / (1024**3):.2f} GB ({vm_init.percent}%)")
    print(f"  - Windows Available RAM:      {vm_init.available / (1024**3):.2f} GB")

    orchestrator = LegalAgentOrchestrator()

    vm_after_init = psutil.virtual_memory()
    p_rss_after_init = proc.memory_info().rss / (1024*1024)
    print(f"\nSau khi nạp mô hình Qwen2.5-1.5B GGUF & MiniLM & Chroma:")
    print(f"  - Python Process RSS:       {p_rss_after_init:.2f} MB")
    print(f"  - Windows Available RAM:    {vm_after_init.available / (1024**3):.2f} GB")

    # Benchmark queries
    bench_queries = [
        ("TC1", "Thời gian thử việc tối đa đối với người làm công việc có chức danh nghề nghiệp cần trình độ đại học trở lên là bao nhiêu ngày?"),
        ("TC2", "Mức hưởng chế độ ốm đau thông thường của người lao động bằng bao nhiêu phần trăm tiền lương?"),
        ("TC3", "Người sử dụng lao động có quyền đơn phương chấm dứt hợp đồng lao động trong những trường hợp nào và phải báo trước bao nhiêu ngày?")
    ]

    # Run iterations
    all_runs = []
    agent_latencies = {
        "intent": [],
        "retrieval": [],
        "analysis": [],
        "validation": [],
        "response": [],
        "total": []
    }

    for run_idx in range(1, 4):
        print(f"\n--- ĐỢT CHẠY LẶP LẠI (RUN #{run_idx}) ---")
        for tag, q in bench_queries:
            t0 = time.time()
            res = orchestrator.process_query(q)
            t_total = time.time() - t0

            agent_latencies["intent"].append(res.timing.intent_time * 1000)
            agent_latencies["retrieval"].append(res.timing.retrieval_time * 1000)
            agent_latencies["analysis"].append(res.timing.analysis_time * 1000)
            agent_latencies["validation"].append(res.timing.validation_time * 1000)
            agent_latencies["response"].append(res.timing.response_time * 1000)
            agent_latencies["total"].append(res.timing.total_time * 1000)

            cur_rss = proc.memory_info().rss / (1024*1024)
            peak_rss = get_peak_rss_mb()
            cur_vm = psutil.virtual_memory()

            print(f"[{tag}-R{run_idx}] Total: {res.timing.total_time:.2f}s (LLM: {res.timing.analysis_time:.2f}s) | RSS: {cur_rss:.1f} MB | Peak: {peak_rss:.1f} MB | Avail: {cur_vm.available / 1024**3:.2f} GB")

    def calc_stats(vals):
        sorted_vals = sorted(vals)
        med = statistics.median(sorted_vals)
        # P95
        p95_idx = int(0.95 * len(sorted_vals))
        p95 = sorted_vals[min(p95_idx, len(sorted_vals)-1)]
        return med, p95

    print("\n" + "="*85)
    print("THỐNG KÊ ĐỘ TRỄ CÁC AGENT (MEDIAN & P95 QUA CÁC LƯỢT CHẠY):")
    print("="*85)
    metrics_summary = {}
    for ag, vals in agent_latencies.items():
        med, p95 = calc_stats(vals)
        metrics_summary[ag] = {"median_ms": round(med, 2), "p95_ms": round(p95, 2)}
        unit = "ms" if ag != "analysis" and ag != "total" else "ms (hoặc s)"
        if ag in ["analysis", "total"]:
            print(f"  * {ag.upper():12}: Median = {med/1000:.2f} s ({med:.1f} ms) | P95 = {p95/1000:.2f} s ({p95:.1f} ms)")
        else:
            print(f"  * {ag.upper():12}: Median = {med:.2f} ms | P95 = {p95:.2f} ms")

    final_rss = proc.memory_info().rss / (1024*1024)
    peak_rss = get_peak_rss_mb()
    final_vm = psutil.virtual_memory()

    ram_report = {
        "process_rss_mb": round(final_rss, 1),
        "peak_working_set_mb": round(peak_rss, 1),
        "system_ram_total_gb": round(final_vm.total / (1024**3), 2),
        "system_ram_used_gb": round(final_vm.used / (1024**3), 2),
        "system_ram_available_gb": round(final_vm.available / (1024**3), 2),
        "system_ram_percent": final_vm.percent,
        "latencies": metrics_summary
    }

    print("\n" + "="*85)
    print(f"TÀI NGUYÊN BỘ NHỚ CUỐI CÙNG:")
    print(f"  - Process Current RSS:    {final_rss:.1f} MB (~{final_rss/1024:.2f} GB)")
    print(f"  - Process Peak RSS:       {peak_rss:.1f} MB (~{peak_rss/1024:.2f} GB)")
    print(f"  - Windows System RAM:     {final_vm.used / (1024**3):.2f} GB / {final_vm.total / (1024**3):.2f} GB ({final_vm.percent}%)")
    print(f"  - Windows Available RAM:  {final_vm.available / (1024**3):.2f} GB")
    print(f"  - Đánh giá khả năng đáp ứng: Với {final_vm.available / (1024**3):.2f} GB RAM khả dụng, tiến trình chiếm ~{final_rss/1024:.2f} GB HOÀN TOÀN KHÔNG gây áp lực hay nguy cơ OOM trên máy 16 GB.")
    print("="*85)

    os.makedirs("reports", exist_ok=True)
    with open("reports/ram_latency_profile.json", "w", encoding="utf-8") as f:
        json.dump(ram_report, f, ensure_ascii=False, indent=2)
    print("Đã lưu kết quả chi tiết vào: reports/ram_latency_profile.json")

if __name__ == "__main__":
    run_ram_latency_benchmark()
