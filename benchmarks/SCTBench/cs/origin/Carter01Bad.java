// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/carter01_bad.c

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class Carter01Bad {
    static Lock m = new ReentrantLock();
    static Lock l = new ReentrantLock();
    static int A = 0, B = 0;

    static void t1() {
        m.lock();
        A++;
        if (A == 1) l.lock();
        m.unlock();
        // perform class A operation
        m.lock();
        A--;
        if (A == 0) l.unlock();
        m.unlock();
    }

    static void t2() {
        m.lock();
        B++;
        if (B == 1) l.lock();
        m.unlock();
        // perform class B operation
        m.lock();
        B--;
        if (B == 0) l.unlock();
        m.unlock();
    }

    static void t3() {
    }

    static void t4() {
    }

    public static void main(String[] args) {
        Thread a1 = new Thread(() -> t1());
        Thread b1 = new Thread(() -> t2());
        Thread a2 = new Thread(() -> t3());
        Thread b2 = new Thread(() -> t4());
        a1.start();
        b1.start();
        a2.start();
        b2.start();
        try {
            a1.join();
            b1.join();
            a2.join();
            b2.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}
