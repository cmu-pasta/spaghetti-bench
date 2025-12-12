// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/sync02_bad.c

import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class Sync02Bad {
  private static final int N = 2;
  private static int num;
  private static Lock m = new ReentrantLock();
  private static Condition empty = m.newCondition();
  private static Condition full = m.newCondition();

  private static void producer() {
    int i = 0;
    while (i < N) {
      m.lock();
      try {
        while (num > 0)
          empty.await();
        num++; // produce
        full.signal();
      } catch (InterruptedException e) {
        e.printStackTrace();
      } finally {
        m.unlock();
      }
      i++;
    }
  }

  private static void consumer() {
    int j = 0;
    while (j < N) {
      m.lock();
      try {
        while (num == 0)
          full.await();
        num--; // consume
        empty.signal();
      } catch (InterruptedException e) {
        e.printStackTrace();
      } finally {
        m.unlock();
      }
      j++;
    }
  }

  public static void main(String[] args) {
    num = 2;

    Thread t1 = new Thread(() -> {
      producer();
    });
    Thread t2 = new Thread(() -> {
      consumer();
    });

    t1.start();
    t2.start();

    try {
      t1.join();
      t2.join();
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
  }
}
