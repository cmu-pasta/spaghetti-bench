// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/arithmetic_prog_bad.c
package cmu.pasta.fray.benchmark.sctbench.cs.origin;

import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class ArithmeticProgBad {
  private static final int N = 3;

  private static int num;
  private static long total;
  private static boolean flag;

  private static ReentrantLock m = new ReentrantLock();
  private static Condition empty = m.newCondition();
  private static Condition full = m.newCondition();

  private static void thread1() {
    int i = 0;
    while (i < N) {
      m.lock();
      try {
        while (num > 0) {
          empty.await();
        }
        num++;
        System.out.println("produce ...." + i);
        full.signal();
      } catch (InterruptedException e) {
        e.printStackTrace();
      } finally {
        m.unlock();
      }

      i++;
    }
  }

  private static void thread2() {
    int j = 0;
    while (j < N) {
      m.lock();
      try {
        while (num == 0) {
          full.await();
        }

        total = total + j;
        System.out.println("total ...." + total);
        num--;
        System.out.println("consume ...." + j);
        empty.signal();
      } catch (InterruptedException e) {
        e.printStackTrace();
      } finally {
        m.unlock();
      }

      j++;
    }
    total = total + j;
    System.out.println("total ...." + total);
    flag = true;
  }

  public static void main(String[] args) {
    num = 0;
    total = 0;

    Thread t1 = new Thread(() -> thread1());
    Thread t2 = new Thread(() -> thread2());

    t1.start();
    t2.start();

    try {
      t1.join();
      t2.join();
    } catch (InterruptedException e) {
      e.printStackTrace();
    }

    if (flag) {
      assert total != ((N * (N + 1)) / 2); // BAD
    }
  }
}
