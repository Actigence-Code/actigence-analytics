# Standalone configuration contract: elixir test/mail_mandatory_test.exs
# Evaluates the actual mail forms with Config.Reader; no application, DB or SMTP.
ExUnit.start()

defmodule ActigenceMailConfigInputs do
  def get_var_from_path_or_env(_directory, name, default \\ nil) do
    Process.get({__MODULE__, :variables}, %{}) |> Map.get(name, default)
  end
end

defmodule ActigenceMailConfigTest do
  use ExUnit.Case, async: false

  @runtime_file Path.expand("../config/runtime.exs", __DIR__)
  @test_file Path.expand("../config/test.exs", __DIR__)

  defp mail_forms do
    {:__block__, _, forms} = @runtime_file |> File.read!() |> Code.string_to_quoted!()

    start_index =
      Enum.find_index(forms, fn
        {:=, _, [{name, _, _}, _]} ->
          name in [:no_delivery_adapter, :actigence_mail_host]

        _ ->
          false
      end)

    end_index =
      Enum.find_index(forms, fn
        {:=, _, [{:base_cron, _, _}, _]} -> true
        _ -> false
      end)

    assert is_integer(start_index), "mail configuration forms must exist"
    assert is_integer(end_index) and end_index > start_index
    Enum.slice(forms, start_index, end_index - start_index)
  end

  defp runtime_config(variables, environment) do
    Process.put({ActigenceMailConfigInputs, :variables}, variables)

    header =
      Code.string_to_quoted!("""
      import Config
      import ActigenceMailConfigInputs
      config_dir = "/unused-by-the-isolated-input-reader"
      """)

    {:__block__, _, header_forms} = header
    source = Macro.to_string({:__block__, [], header_forms ++ mail_forms()})
    Config.Reader.eval!(@runtime_file, source, env: environment)
  after
    Process.delete({ActigenceMailConfigInputs, :variables})
  end

  defp mail_config(variables, environment \\ :prod) do
    runtime_config(variables, environment)
    |> Keyword.fetch!(:plausible)
    |> Keyword.fetch!(Plausible.Mailer)
  end

  test "production submission uses the private relay and no provider credentials" do
    for host <- ["127.0.0.1", "100.72.162.79", "10.77.0.1", "10.77.255.254"] do
      config = mail_config(%{"ACTIGENCE_MAIL_RELAY_HOST" => host})
      assert config[:adapter] == Bamboo.Mua
      assert config[:relay] == host
      assert config[:port] == 25
      assert config[:protocol] == :tcp
      refute Keyword.has_key?(config, :auth)
      refute Keyword.has_key?(config, :username)
      refute Keyword.has_key?(config, :password)
    end
  end

  test "DNS prefix attacks, invalid literals and unapproved endpoints fail closed" do
    for host <- [
          "10.77.smtp.attacker.example",
          "10.77..evil",
          "10.77.1.1.evil.example",
          "10.77.999.999",
          "10.77.-1.1",
          "10.77.1.1:25",
          "10.77.1.1.",
          "127.0.0.2",
          "172.17.0.1",
          "192.168.1.1",
          "8.8.8.8",
          "0.0.0.0",
          "localhost",
          "mail-eu.smtp2go.com",
          "smtp://10.77.0.1",
          "::1",
          "::ffff:10.77.0.1",
          "",
          " 10.77.0.1",
          "10.77.0.1\n"
        ] do
      assert_raise ArgumentError, "actigence_mail_relay_unavailable", fn ->
        mail_config(%{"ACTIGENCE_MAIL_RELAY_HOST" => host})
      end
    end
  end

  test "known delivering provider choices cannot choose another transport" do
    for adapter <- [
          "Bamboo.MailgunAdapter",
          "Bamboo.PostmarkAdapter",
          "Bamboo.MandrillAdapter",
          "Bamboo.SendGridAdapter",
          "Bamboo.SMTPAdapter",
          "Bamboo.Mua"
        ] do
      config =
        mail_config(%{
          "MAILER_ADAPTER" => adapter,
          "SMTP_HOST" => "external.example.invalid",
          "SMTP_RELAY" => "external.example.invalid",
          "SMTP_PORT" => "465",
          "SMTP_PROTOCOL" => "ssl",
          "SMTP_USERNAME" => "old-synthetic-user",
          "SMTP_PASSWORD" => "old-synthetic-password",
          "SMTP_HOST_ADDR" => "mail-eu.smtp2go.com",
          "SMTP_HOST_PORT" => "443",
          "SMTP_HOST_SSL_ENABLED" => "true",
          "SMTP_USER_NAME" => "legacy-synthetic-user",
          "SMTP_USER_PWD" => "legacy-synthetic-password"
        })

      assert config == [adapter: Bamboo.Mua, relay: "127.0.0.1", port: 25, protocol: :tcp]
    end
  end

  test "unknown adapters fail closed without evaluating arbitrary module names" do
    for environment <- [:prod, :ce, :dev, :test, :ce_test, :e2e_test],
        adapter <- ["unknown", "Bamboo.FakeAdapter", ""] do
      assert_raise ArgumentError, "Unknown mailer_adapter: #{inspect(adapter)}", fn ->
        mail_config(%{"MAILER_ADAPTER" => adapter}, environment)
      end
    end
  end

  test "invalid relay never falls back to a provider or a second endpoint" do
    assert_raise ArgumentError, "actigence_mail_relay_unavailable", fn ->
      mail_config(%{
        "MAILER_ADAPTER" => "Bamboo.PostmarkAdapter",
        "ACTIGENCE_MAIL_RELAY_HOST" => "10.77.smtp.attacker.example",
        "SMTP_HOST" => "mail-eu.smtp2go.com",
        "SMTP_PROTOCOL" => "tls"
      })
    end
  end

  test "explicit native non-delivery adapters survive every environment" do
    for environment <- [:prod, :ce, :dev, :test, :ce_test, :e2e_test],
        {setting, adapter} <- [
          {"Bamboo.TestAdapter", Bamboo.TestAdapter},
          {"Bamboo.LocalAdapter", Bamboo.LocalAdapter}
        ],
        host <- ["127.0.0.1", "deliberately.invalid"] do
      config =
        mail_config(
          %{
            "MAILER_ADAPTER" => setting,
            "ACTIGENCE_MAIL_RELAY_HOST" => host
          },
          environment
        )

      assert config == [adapter: adapter]
    end
  end

  test "native test environments never gain SMTP through runtime configuration" do
    for environment <- [:test, :ce_test, :e2e_test],
        adapter <- [nil, "Bamboo.Mua", "Bamboo.MailgunAdapter"],
        host <- [nil, "deliberately.invalid"] do
      variables = if host, do: %{"ACTIGENCE_MAIL_RELAY_HOST" => host}, else: %{}
      variables = if adapter, do: Map.put(variables, "MAILER_ADAPTER", adapter), else: variables

      native = Config.Reader.read!(@test_file, env: environment)
      effective = Config.Reader.merge(native, runtime_config(variables, environment))
      assert get_in(effective, [:plausible, Plausible.Mailer]) == [adapter: Bamboo.TestAdapter]
    end
  end
end
