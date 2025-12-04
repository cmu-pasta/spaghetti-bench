// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/twostage_bad.c
package cmu.pasta.fray.benchmark.sctbench.cs.origin;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class TwostageBad {
    private static final String USAGE = "./twostage <param1> <param2>\n";
    
    private static int iTThreads = 1;
    private static int iRThreads = 1; 
    private static int data1Value = 0;
    private static int data2Value = 0;
    private static Lock data1Lock = new ReentrantLock();
    private static Lock data2Lock = new ReentrantLock();
    
    private static void funcA() {
        data1Lock.lock();
        try {
            data1Value = 1;
        } finally {
            data1Lock.unlock();
        }
        
        data2Lock.lock();
        try {
            data2Value = data1Value + 1;
        } finally {
            data2Lock.unlock();
        }
    }
    
    private static void funcB() {
        int t1 = -1;
        int t2 = -1;
        
        data1Lock.lock();
        try {
            if (data1Value == 0) {
                return;
            }
            t1 = data1Value;
        } finally {
            data1Lock.unlock();
        }
        
        data2Lock.lock();
        try {
            t2 = data2Value;
        } finally { 
            data2Lock.unlock();
        }
        
        if (t2 != (t1 + 1)) {
            System.err.println("Bug found!");
            assert false; /* BAD */
        }
    }
    
    public static void main(String[] args) {
        iTThreads = 1;
        iRThreads = 1;
        data1Value = 0;
        data2Value = 0;
        
        Thread[] tPool = new Thread[iTThreads];
        Thread[] rPool = new Thread[iRThreads];
        
        for (int i = 0; i < iTThreads; i++) {
            tPool[i] = new Thread(() -> funcA());
            tPool[i].start();
        }
        
        for (int i = 0; i < iRThreads; i++) {
            rPool[i] = new Thread(() -> funcB());
            rPool[i].start(); 
        }
        
        for (int i = 0; i < iTThreads; i++) {
            try {
                tPool[i].join();
            } catch (InterruptedException e) {
                System.err.println("Thread join interrupted");
                throw new RuntimeException();
            }
        }
        
        for (int i = 0; i < iRThreads; i++) {
            try {
                rPool[i].join();
            } catch (InterruptedException e) {
                System.err.println("Thread join interrupted");
                throw new RuntimeException();
            }
        }
    }
}