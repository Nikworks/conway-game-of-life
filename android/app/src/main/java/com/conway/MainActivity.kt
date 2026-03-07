package com.conway

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.web_view)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            // Allow mixed content for local development
            @Suppress("DEPRECATION")
            allowFileAccess = true
        }
        // Handle redirects in-app instead of opening the browser
        webView.webViewClient = WebViewClient()

        loadServerUrl()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.menu_main, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_settings -> {
                startActivity(Intent(this, SettingsActivity::class.java))
                true
            }
            R.id.action_reload -> {
                loadServerUrl()
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    private fun loadServerUrl() {
        val prefs = getSharedPreferences("conway_prefs", MODE_PRIVATE)
        // 10.0.2.2 is the Android emulator loopback address for the host machine
        val url = prefs.getString("server_url", "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000"
        webView.loadUrl(url)
    }
}
