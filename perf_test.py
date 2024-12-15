import multiprocessing
import time
import os

def heavy_computation(x):
    """Simulates a heavy computation task."""
    result = 0
    for _ in range(20000000):  # Simulate computational load
        result += x * x
    return result

def measure_performance(num_processes, task_data):
    """Measure the execution time using multiprocessing."""
    start_time = time.time()
    with multiprocessing.Pool(num_processes) as pool:
        pool.map(heavy_computation, task_data)
    end_time = time.time()
    return end_time - start_time

def generate_report(report_data):
    """Generate a performance report."""
    report_lines = [
        "Multiprocessing Performance Test Report",
        "-" * 50,
        "Number of Processes | Execution Time (s) | Speedup vs Single Process"
    ]
    for num_processes, exec_time, speedup in report_data:
        report_lines.append(f"{num_processes:^19} | {exec_time:^18.4f} | {speedup:^25.2f}")
    return "\n".join(report_lines)

if __name__ == "__main__":
    # Parameters for the performance test
    data_size = 16  # Number of tasks to simulate
    task_data = list(range(data_size))  # Dummy input data for tasks
    max_processes = min(data_size, os.cpu_count())  # Limit to available CPUs

    # Run performance tests
    report_data = []
    single_process_time = measure_performance(1, task_data)
    report_data.append((1, single_process_time, 1.0))  # Baseline: single process

    for num_processes in range(2, max_processes + 1):
        exec_time = measure_performance(num_processes, task_data)
        speedup = single_process_time / exec_time if exec_time > 0 else float('inf')
        report_data.append((num_processes, exec_time, speedup))

    # Generate and display the report
    report = generate_report(report_data)
    print(report)

    # Save report to a file
    with open("multiprocessing_performance_report.txt", "w") as file:
        file.write(report)
