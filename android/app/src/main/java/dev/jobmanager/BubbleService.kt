package dev.jobmanager

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.graphics.PixelFormat
import android.os.Build
import android.os.IBinder
import android.provider.Settings
import android.view.Gravity
import android.view.WindowManager
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.LinearLayout

class BubbleService : Service() {

    private lateinit var windowManager: WindowManager
    private lateinit var bubbleView: ImageButton
    private lateinit var panelView: LinearLayout
    private lateinit var webView: WebView

    private val bubbleParams = WindowManager.LayoutParams(
        WindowManager.LayoutParams.WRAP_CONTENT,
        WindowManager.LayoutParams.WRAP_CONTENT,
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else
            WindowManager.LayoutParams.TYPE_PHONE,
        WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
        PixelFormat.TRANSLUCENT
    ).apply {
        gravity = Gravity.TOP or Gravity.START
        x = 24
        y = 320
    }

    private val panelParams = WindowManager.LayoutParams(
        FrameLayout.LayoutParams.MATCH_PARENT,
        FrameLayout.LayoutParams.MATCH_PARENT,
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        else
            WindowManager.LayoutParams.TYPE_PHONE,
        WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
        PixelFormat.TRANSLUCENT
    ).apply {
        gravity = Gravity.TOP
        x = 0
        y = 0
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(Context.WINDOW_SERVICE) as WindowManager
        createNotificationChannel()
        startAsForeground()
        buildBubble()
        showBubble()
    }

    override fun onDestroy() {
        super.onDestroy()
        removeViewsIfPresent()
        webView.destroy()
    }

    @SuppressLint("InflateParams")
    private fun buildBubble() {
        bubbleView = ImageButton(this).apply {
            setImageResource(android.R.drawable.ic_dialog_info)
            backgroundTintList = android.content.res.ColorStateList.valueOf(Color.rgb(34, 211, 238))
            setOnClickListener { togglePanel() }
            elevation = 12f
        }
        panelView = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(15, 23, 42))
        }
        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            webChromeClient = WebChromeClient()
            webViewClient = WebViewClient()
        }
        panelView.addView(
            webView,
            LinearLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
            )
        )
    }

    private fun showBubble() {
        if (bubbleView.isAttachedToWindow) return
        windowManager.addView(bubbleView, bubbleParams)
    }

    private fun togglePanel() {
        val isVisible = panelView.isAttachedToWindow
        if (isVisible) {
            windowManager.removeView(panelView)
        } else {
            loadJobBotUrl()
            windowManager.addView(panelView, panelParams)
        }
    }

    private fun loadJobBotUrl() {
        val prefs = getSharedPreferences("jobmanager", Context.MODE_PRIVATE)
        val baseUrl = prefs.getString("base_url", "http://192.168.1.10:5173").orEmpty()
        webView.loadUrl(baseUrl)
    }

    private fun removeViewsIfPresent() {
        try {
            if (bubbleView.isAttachedToWindow) windowManager.removeView(bubbleView)
        } catch (ignored: Exception) {
        }
        try {
            if (panelView.isAttachedToWindow) windowManager.removeView(panelView)
        } catch (ignored: Exception) {
        }
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "JobBot floating bubble",
            NotificationManager.IMPORTANCE_LOW
        )
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    private fun startAsForeground() {
        val openIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        val notification = Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("JobBot is ready")
            .setContentText("Tap the bubble to open JobBot")
            .setContentIntent(openIntent)
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .build()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    companion object {
        private const val CHANNEL_ID = "jobbot_bubble"
        private const val NOTIFICATION_ID = 1001
    }
}