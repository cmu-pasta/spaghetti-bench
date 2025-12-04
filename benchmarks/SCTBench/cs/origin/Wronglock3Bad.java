package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/wronglock_3_bad.c

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class Wronglock3Bad {
    private static int iNum1 = 1;
    private static int iNum2 = 3;
    private static volatile int dataValue = 0;
    private static Lock dataLock;
    private static Lock thisLock;

    public static void main(String[] args) {
        int i;

        dataValue = 0;
        dataLock = new ReentrantLock();
        thisLock = new ReentrantLock();

        Thread[] num1Pool = new Thread[iNum1];
        Thread[] num2Pool = new Thread[iNum2];

        for (i = 0; i < iNum1; i++) {
            final int id = i;
            num1Pool[i] = new Thread(() -> funcA(id));
            num1Pool[i].start();
        }

        for (i = 0; i < iNum2; i++) {
            final int id = i;
            num2Pool[i] = new Thread(() -> funcB(id));
            num2Pool[i].start();
        }

        for (i = 0; i < iNum1; i++) {
            try {
                num1Pool[i].join();
            } catch (InterruptedException e) {
                System.err.println("Thread join interrupted: " + e);
                throw new RuntimeException();
            }
        }

        for (i = 0; i < iNum2; i++) {
            try {
                num2Pool[i].join();
            } catch (InterruptedException e) {
                System.err.println("Thread join interrupted: " + e);
                throw new RuntimeException();
            }
        }
    }

    private static void funcA(int id) {
        lock(dataLock);
        int x = dataValue;
        dataValue++;
        if (dataValue != (x + 1)) {
            System.err.println("Bug Found!");
            assert false;
        }
        unlock(dataLock);
    }

    private static void funcB(int id) {
        lock(thisLock);
        dataValue++; 
        unlock(thisLock);
    }

    private static void lock(Lock lock) {
        lock.lock();
    }

    private static void unlock(Lock lock) {
        lock.unlock();
    }
}
