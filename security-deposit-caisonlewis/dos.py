import multiprocessing
import urllib.request


def attack(thread_id):
    print("Spawning attack thread", thread_id)
    for _ in range(100000):
        urllib.request.urlopen("http://127.0.0.1:9999/")  # nosec
    print("Thread finished!")


if __name__ == "__main__":
    threads = []

    for i in range(0, 128):
        process = multiprocessing.Process(target=attack, args=(i,))
        threads.append(process)

    for t in threads:
        t.start()

    for t in threads:
        t.join()
