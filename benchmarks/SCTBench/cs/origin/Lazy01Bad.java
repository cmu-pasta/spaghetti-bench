package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/lazy01_bad.c

import java.util.concurrent.locks.ReentrantLock;

public class Lazy01Bad {
    
    private static ReentrantLock mutex = new ReentrantLock();
    private static int data = 0;

    private static void thread1() {
        mutex.lock();
        try {
            data++;
        } finally {
            mutex.unlock();
        }
    }

    private static void thread2() {
        mutex.lock();
        try {
            data += 2;
        } finally {
            mutex.unlock();
        }
    }

    private static void thread3() {
        mutex.lock();
        try {
            if (data >= 3) {
                assert false; // BAD
            }
        } finally {
            mutex.unlock();
        }
    }

    public static void main(String[] args) {
        Thread t1 = new Thread(() -> thread1());
        Thread t2 = new Thread(() -> thread2());
        Thread t3 = new Thread(() -> thread3());

        t1.start();
        t2.start();
        t3.start();

        try {
            t1.join();
            t2.join();  
            t3.join();
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }
}