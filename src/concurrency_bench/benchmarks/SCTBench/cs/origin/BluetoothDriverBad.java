// Translated from: https://github.com/mc-imperial/sctbench/blob/d59ab26ddaedcd575ffb6a1f5e9711f7d6d2d9f2/benchmarks/concurrent-software-benchmarks/bluetooth_driver_bad.c

package cmu.pasta.fray.benchmark.sctbench.cs.origin;

public class BluetoothDriverBad {
    private static final boolean TRUE = true;
    private static final boolean FALSE = false;
    
    private static boolean stopped;

    private static class Device {
        int pendingIo;
        boolean stoppingFlag;
        boolean stoppingEvent;
    }

    private static int BCSP_IoIncrement(Device e) {
        if (e.stoppingFlag)
            return -1;

        synchronized (e) {
            e.pendingIo = e.pendingIo + 1;
        }

        return 0;
    }

    private static void BCSP_IoDecrement(Device e) {
        int pendingIo;

        synchronized (e) {
            e.pendingIo = e.pendingIo - 1;
            pendingIo = e.pendingIo;
        }

        if (pendingIo == 0) 
            e.stoppingEvent = TRUE;
    }

    private static void BCSP_PnpAdd(Device e) {
        int status = BCSP_IoIncrement(e);
        if (status == 0) {
            // do work here
            assert !stopped;
        }
        BCSP_IoDecrement(e);
    }

    private static void BCSP_PnpStop(Device e) {
        e.stoppingFlag = TRUE;
        BCSP_IoDecrement(e); 
        if (e.stoppingEvent) {
            // release allocated resource
            stopped = TRUE;
        }
    }

    public static void main(String[] args) {
        Device e = new Device();

        e.pendingIo = 1;
        e.stoppingFlag = FALSE;
        e.stoppingEvent = FALSE;
        stopped = FALSE;

        Thread thread = new Thread(() -> BCSP_PnpStop(e));
        thread.start();
        BCSP_PnpAdd(e);
        try {
            thread.join();
        } catch (InterruptedException ex) {
            ex.printStackTrace();
        }
    }
}
