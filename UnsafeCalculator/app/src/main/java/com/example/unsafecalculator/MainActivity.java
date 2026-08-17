package com.example.unsafecalculator;

import android.Manifest;
import android.content.pm.PackageManager;
import android.hardware.camera2.CameraManager;
import android.location.LocationManager;
import android.media.MediaRecorder;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

public class MainActivity extends AppCompatActivity {

    private static final int REQUEST_CODE = 100;

    private final String[] unnecessaryPermissions = {
            Manifest.permission.CAMERA,
            Manifest.permission.ACCESS_FINE_LOCATION,
            Manifest.permission.READ_CONTACTS,
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.READ_SMS
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        TextView tvDisplay = findViewById(R.id.tvDisplay);
        EditText etNum1 = findViewById(R.id.etNum1);
        EditText etNum2 = findViewById(R.id.etNum2);

        ActivityCompat.requestPermissions(this, unnecessaryPermissions, REQUEST_CODE);

        touchCameraApi();
        touchLocationApi();
        touchMicrophoneApi();

        findViewById(R.id.btnAdd).setOnClickListener(v -> {
            double result = num(etNum1) + num(etNum2);
            tvDisplay.setText(String.valueOf(result));
        });

        findViewById(R.id.btnSubtract).setOnClickListener(v -> {
            double result = num(etNum1) - num(etNum2);
            tvDisplay.setText(String.valueOf(result));
        });

        findViewById(R.id.btnMultiply).setOnClickListener(v -> {
            double result = num(etNum1) * num(etNum2);
            tvDisplay.setText(String.valueOf(result));
        });

        findViewById(R.id.btnDivide).setOnClickListener(v -> {
            double n2 = num(etNum2);
            if (n2 != 0.0) {
                tvDisplay.setText(String.valueOf(num(etNum1) / n2));
            } else {
                tvDisplay.setText("Error");
            }
        });
    }

    private double num(EditText e) {
        String text = e.getText().toString();
        try {
            return Double.parseDouble(text);
        } catch (NumberFormatException ex) {
            return 0.0;
        }
    }

    private void touchCameraApi() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) return;
        try {
            CameraManager cameraManager = (CameraManager) getSystemService(CAMERA_SERVICE);
            cameraManager.getCameraIdList();
        } catch (Exception ignored) { }
    }

    private void touchLocationApi() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) return;
        try {
            LocationManager locationManager = (LocationManager) getSystemService(LOCATION_SERVICE);
            locationManager.getProviders(true);
        } catch (Exception ignored) { }
    }

    private void touchMicrophoneApi() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) return;
        try {
            MediaRecorder recorder = new MediaRecorder();
            recorder.setAudioSource(MediaRecorder.AudioSource.MIC);
            recorder.release();
        } catch (Exception ignored) { }
    }
}