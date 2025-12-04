package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/carter01_bad.c

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class Carter01Bad {
    static Lock m = new ReentrantLock();
    static Lock l = new ReentrantLock(); 
    static int A = 0, B = 0;
    static boolean mLockedBy1 = false;
    static boolean mLockedBy2 = false;
    static boolean lLockedBy1 = false;
    static boolean lLockedBy2 = false;

    static void t1() {
        try {
            m.lock();
            mLockedBy1 = true;
            A++;
            if (A == 1) {
                l.lock();
                lLockedBy1 = true;
            }
            m.unlock();
            mLockedBy1 = false;

            do {
                if (mLockedBy2 && lLockedBy1) {
                    System.out.println("Deadlock detected");
                    throw new RuntimeException();
                }
            } while (!m.tryLock());
            A--;
            if (A == 0) {
                l.unlock();
                lLockedBy1 = false;
            }
            m.unlock();
        } finally {
            if (mLockedBy1) {
                m.unlock();
                mLockedBy1 = false;
            }
            if (lLockedBy1) {
                l.unlock();
                lLockedBy1 = false;
            }
        }
    }

    static void t2() {
        try {
            m.lock();
            mLockedBy2 = true;
            B++;
            if (B == 1) {
                l.lock();
                lLockedBy2 = true;
            }
            m.unlock();
            mLockedBy2 = false;

            do {
                if (mLockedBy1 && lLockedBy2) {
                    System.out.println("Deadlock detected");
                    throw new RuntimeException();
                }
                // perform class B operation
            } while (!m.tryLock());
            B--;
            if (B == 0) {
                l.unlock();
                lLockedBy2 = false;
            }
            m.unlock();
        } finally {
            if (mLockedBy2) {
                m.unlock();
                mLockedBy2 = false;
            }
            if (lLockedBy2) {
                l.unlock();
                lLockedBy2 = false;
            }
        }
    }

    static void t3() {
    }

    static void t4() {
    }

    public static void main(String[] args) {
        m = new ReentrantLock();
        l = new ReentrantLock();
        A = 0;
        B = 0;
        mLockedBy1 = false;
        mLockedBy2 = false;
        lLockedBy1 = false;
        lLockedBy2 = false;
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