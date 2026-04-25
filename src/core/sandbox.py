import multiprocessing
import ast
from typing import Dict, Any, List

def run_user_code(code: str, args: List[Any], queue: multiprocessing.Queue):
    """
    Sub-process target to parse user code and execute the primary function.
    """
    try:
        local_scope = {}
        exec(code, {}, local_scope)
        # Discover the defined function (assume last defined function is the target solution)
        functions = [v for k, v in local_scope.items() if callable(v) and not k.startswith('__')]
        if not functions:
            queue.put({"success": False, "error": "No function defined in code."})
            return
        
        target_fn = functions[-1]
        res = target_fn(*args)
        queue.put({"success": True, "result": res})
    except Exception as e:
        queue.put({"success": False, "error": str(e)})

def run_tests_on_code(submitted_code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, bool]:
    """
    Spawns isolated processes per test-case to sandbox infinite loops / crashes safely via timeout.
    Returns tracking dict {"t1": True, "t2": False}.
    """
    execution_results = {}
    
    for i, tc in enumerate(test_cases):
        test_id = f"t{i+1}"
        args = tc.get("args", tc.get("input", []))
        if not isinstance(args, list):
            args = [args]
            
        expected = tc.get("expected", tc.get("output"))
        
        queue = multiprocessing.Queue()
        proc = multiprocessing.Process(target=run_user_code, args=(submitted_code, args, queue))
        proc.start()
        proc.join(timeout=2.0)
        
        if proc.is_alive():
            proc.terminate()
            proc.join()
            execution_results[test_id] = False
            continue
            
        if not queue.empty():
            out = queue.get()
            if out.get("success"):
                execution_results[test_id] = (out.get("result") == expected)
            else:
                execution_results[test_id] = False
        else:
            execution_results[test_id] = False
            
    return execution_results
