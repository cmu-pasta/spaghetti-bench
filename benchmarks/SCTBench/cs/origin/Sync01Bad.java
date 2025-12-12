package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/sync01_bad.c

import java.lang.management.ManagementFactory;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.concurrent.locks.Condition;

public class Sync01Bad {
    static final int N = 1;

    static int num;

    static Lock m = new ReentrantLock();
    static Condition empty = m.newCondition();
    static Condition full = m.newCondition();

    static void thread1() {
        m.lock();
        try {
            while (num > 0) {
                Thread t = new Thread(() -> {
                    m.lock(); // make sure t is executed after empty.await();
                    int activeCount = Thread.activeCount();
                    m.unlock();
                    if (activeCount == 3) {
                        System.out.println("Deadlock detected");
                        System.exit(1);
                    }
                });
                t.start();
                empty.await();  // BAD: deadlock
            }
            num++;
            full.signal();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            m.unlock();
        }
    }

    static void thread2() {
        m.lock();
        try {
            while (num == 0) {
                full.await();
            }
            empty.signal();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            m.unlock();
        }
    }

    public static void main(String[] args) {
        num = 1;

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
    }
}
