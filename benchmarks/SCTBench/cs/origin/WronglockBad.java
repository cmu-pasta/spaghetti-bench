package cmu.pasta.fray.benchmark.sctbench.cs.origin;

// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/wronglock_bad.c

import java.util.concurrent.locks.ReentrantLock;

public class WronglockBad {
    private static final String USAGE = "./wronglock <param1> <param2>\n";
    
    private static int iNum1 = 1;
    private static int iNum2 = 7;
    private static volatile int dataValue = 0;
    private static ReentrantLock dataLock;
    private static ReentrantLock thisLock;

    private static void lock(ReentrantLock lock) {
        lock.lock();
    }

    private static void unlock(ReentrantLock lock) {
        lock.unlock();
    }

    private static void funcA() {
        lock(dataLock);
        int x = dataValue;
        dataValue++;
        if (dataValue != (x+1)) {
            System.err.println("Bug Found!");
            assert false; // BAD
        }
        unlock(dataLock);
    }

    private static void funcB() {
        lock(thisLock);
        dataValue++;
        unlock(thisLock);
    }

    public static void main(String[] args) {
        dataValue = 0;

        dataLock = new ReentrantLock();
        thisLock = new ReentrantLock();

        Thread[] num1Pool = new Thread[iNum1];
        Thread[] num2Pool = new Thread[iNum2];

        for (int i = 0; i < iNum1; i++) {
            num1Pool[i] = new Thread(() -> {
                funcA();
            });
            num1Pool[i].start();
        }

        for (int i = 0; i < iNum2; i++) {
            num2Pool[i] = new Thread(() -> {
                funcB();
            });
            num2Pool[i].start();
        }

        for (int i = 0; i < iNum1; i++) {
            try {
                num1Pool[i].join();
            } catch (InterruptedException e) {
                System.err.println("Thread join error: " + e.getMessage());
                throw new RuntimeException();
            }
        }

        for (int i = 0; i < iNum2; i++) {
            try {
                num2Pool[i].join();
            } catch (InterruptedException e) {
                System.err.println("Thread join error: " + e.getMessage());
                throw new RuntimeException();
            }
        }
    }
}