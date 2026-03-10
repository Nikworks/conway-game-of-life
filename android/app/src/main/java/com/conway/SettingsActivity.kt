package com.conway

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class SettingsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        val prefs = getSharedPreferences("conway_prefs", MODE_PRIVATE)
        val urlInput = findViewById<EditText>(R.id.et_server_url)
        val saveBtn = findViewById<Button>(R.id.btn_save)

        // Pre-fill with current value
        urlInput.setText(
            prefs.getString("server_url", "http://10.0.2.2:8000")
        )

        saveBtn.setOnClickListener {
            val url = urlInput.text.toString().trim()
            if (url.isEmpty()) {
                urlInput.error = getString(R.string.error_url_empty)
                return@setOnClickListener
            }
            prefs.edit().putString("server_url", url).apply()
            Toast.makeText(this, getString(R.string.saved), Toast.LENGTH_SHORT).show()
            finish()
        }
    }
}
